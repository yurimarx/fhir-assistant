Class fhirtemplate.Setup Extends %RegisteredObject
{

ClassMethod SetupFHIRServer(ns = "FHIRSERVER", appKey = "/fhir/r4", testLoad = 1, interactionsStrategy As %String(VALUELIST=",Json,JsonAdvSql") = "Json") As %Status
{
    Set st=$$$OK
    Write !,"=== Initialization with parameters: Namespace: "_ns_", Webapp: "_appKey_", AddTestData: "_testLoad,!
    ZNspace "HSLIB"
    Set namespace=ns
    ;Set appKey = "/fhir/r4"
    If interactionsStrategy = "Json" {
        Set strategyClass = "HS.FHIRServer.Storage.Json.InteractionsStrategy"
    } ElseIf interactionsStrategy = "JsonAdvSql" {
        Set strategyClass = "HS.FHIRServer.Storage.JsonAdvSQL.InteractionsStrategy"
    }
    Set metadataPackages = $LISTBUILD("hl7.fhir.r4.core@4.0.1")
    Set metadataConfigKey = "HL7v40"
    ;set importdir="/opt/irisapp/src"

    //Install a Foundation namespace and change to it
    //Do ##class(HS.HC.Util.Installer).InstallFoundation(namespace)
    Do ##class(HS.Util.Installer.Foundation).Install(namespace)

    ZNspace namespace

    // Install elements that are required for a FHIR-enabled namespace
    Do ##class(HS.FHIRServer.Installer).InstallNamespace()

    // Install an instance of a FHIR Service into the current namespace
    If '##class(HS.FHIRServer.ServiceAdmin).EndpointExists(appKey) {
       Do ##class(HS.FHIRServer.Installer).InstallInstance(appKey, strategyClass, metadataPackages)
    }

    Set strategy = ##class(HS.FHIRServer.API.InteractionsStrategy).GetStrategyForEndpoint(appKey)
    Set config = strategy.GetServiceConfigData()
    Set config.DebugMode = 4
    Do strategy.SaveServiceConfigData(config)

    If testLoad {
        Set dir=$SYSTEM.Util.ManagerDirectory()_"test-data-fhir"
        Write !," ====== Load test data in "_ns_" from "_dir
        Set st=##class(HS.FHIRServer.Tools.DataLoader).SubmitResourceFiles(dir, "FHIRServer", appKey)
        
        If 'st {
            Write $SYSTEM.Status.GetErrorText(st) 
        } Else {
            // Do ..VectorizePatients()
        }
    }

    Quit st
}

ClassMethod LoadPatientData(path, namespace, appKey) As %Status
{
    Quit ##class(HS.FHIRServer.Tools.DataLoader).SubmitResourceFiles(path, namespace, appKey)
}

ClassMethod AddApp(ns = {$NAMESPACE}) As %Status
{
    Set namespace=ns
    ZNspace "%SYS"
    Set webName = "/fhirUI"
    Set webProperties("NameSpace") = namespace
    Set webProperties("Enabled") = 1
    Set webProperties("Path") = "/irisdev/app/fhirUI"
    Set webProperties("AutheEnabled") = 64
    Set webProperties("ServeFiles")=2
    Set webProperties("Recurse")=1
    Quit ##class(Security.Applications).Create(webName, .webProperties)
}

ClassMethod VectorizePatients(fhirUrl As %String = "http://iris:52773/fhir/r4", user As %String = "SuperUser", pwd As %String = "SYS", ollamaUrl As %String = "http://ollama:11434", model As %String = "llama3") [ Language = python ]
{
    import iris
    import requests
    import json

    print("Starting the vectorization of patient summaries...")
    for patient_id in range(1, 8):
        try:
            # 1. Get Patient data
            pat_url = f"{fhirUrl}/Patient/{patient_id}"
            print(pat_url)
            pat_resp = requests.get(pat_url, auth=(user, pwd), timeout=10)
            if pat_resp.status_code != 200:
                print(f"Patient {patient_id} not found.")
                continue
            patient_data = pat_resp.json()
            
            # 2. Get Observations associated with the Patient
            obs_url = f"{fhirUrl}/Observation?patient={patient_id}"
            obs_resp = requests.get(obs_url, auth=(user, pwd), timeout=10)
            obs_data = obs_resp.json() if obs_resp.status_code == 200 else {}
            
            # 3. Build Clinical Summary in text
            name = "Unknown"
            if "name" in patient_data and len(patient_data["name"]) > 0:
                name_dict = patient_data["name"][0]
                name = name_dict.get("given", [""])[0] + " " + name_dict.get("family", "")
                
            summary = f"Patient: {name.strip()} (ID: {patient_id}), "
            summary += f"Gender: {patient_data.get('gender', 'unknown')}, "
            summary += f"BirthDate: {patient_data.get('birthDate', 'unknown')}. "
            
            observations = []
            for entry in obs_data.get("entry", []):
                res = entry.get("resource", {})
                code_text = res.get("code", {}).get("text", "Unknown")
                if "valueQuantity" in res:
                    val = res["valueQuantity"].get("value", "")
                    unit = res["valueQuantity"].get("unit", "")
                    observations.append(f"{code_text}: {val} {unit}")
                elif "valueCodeableConcept" in res:
                    val = res["valueCodeableConcept"].get("text", "")
                    observations.append(f"{code_text}: {val}")
            
            if observations:
                summary += "Observations: " + "; ".join(observations) + "."
            else:
                summary += "No observations found."
                
            # 4. Generate Embeddings using Ollama
            emb_payload = {
                "model": model,
                "prompt": summary
            }
            emb_resp = requests.post(f"{ollamaUrl}/api/embeddings", json=emb_payload, timeout=30)
            if emb_resp.status_code == 200:
                vector = emb_resp.json()["embedding"] 
                conn_string = "iris:1972/FHIRSERVER"
                username = user
                password = pwd
                connection = iris.connect(conn_string, username, password)
                cursor = connection.cursor()
                
                # 5. Save the summary using SQL
                try:
                    sql = "INSERT OR UPDATE INTO SQLUser.PatientSummary (PatientId, Summary, SummaryVector) VALUES (?, ?, TO_VECTOR(?))"
                    params = [str(patient_id), summary, str(vector)]
                    cursor.execute(sql,params)
                    cursor.close()
                    print(f"Patient {patient_id} vectorized and saved successfully using SQL.")
                except Exception as ex:
                    print(f"Error saving Patient {patient_id}: {ex}")
                finally:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()
            else:
                print(f"Error obtaining Ollama embedding for patient {patient_id}: {emb_resp.text}")
                
        except Exception as e:
            print(f"Error processing patient {patient_id}: {e}")
}

}
