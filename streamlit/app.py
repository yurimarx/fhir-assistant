import streamlit as st
import requests
import json
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="Smart Patient Summary Generator", layout="wide")

IRIS_FHIR_URL = st.sidebar.text_input("IRIS FHIR Endpoint Local", "http://iris:52773/fhir/r4")
IRIS_USER = st.sidebar.text_input("Username", "SuperUser")
IRIS_PASSWORD = st.sidebar.text_input("Password", "SYS", type="password")
OLLAMA_URL = st.sidebar.text_input("Ollama Endpoint", "http://ollama:11434")
MODEL_NAME = st.sidebar.selectbox("LLM Model", ["llama3"])

def fetch_patient_fhir_bundle(patient_id: str) -> dict:
    """
    Fetches the patient's FHIR resource bundle from InterSystems IRIS.
    For the MVP, we consolidate the essential resources into a single bundle or dictionary.
    """
    headers = {"Accept": "application/fhir+json"}
    auth = (IRIS_USER, IRIS_PASSWORD)
    
    resources = ["Patient", "Condition", "MedicationRequest", "AllergyIntolerance", "Observation", "Encounter", "CarePlan"]
    patient_data = {}
    
    try:
        for res in resources:
            if res == "Patient":
                url = f"{IRIS_FHIR_URL}/Patient/{patient_id}"
            else:
                url = f"{IRIS_FHIR_URL}/{res}?patient={patient_id}&_count=10"
                
            response = requests.get(url, headers=headers, auth=auth, timeout=5)
            if response.status_code == 200:
                patient_data[res] = response.json()
            else:
                patient_data[res] = None
                
        return patient_data
    except Exception as e:
        st.error(f"Error connecting to InterSystems IRIS: {e}")

PERSONA_PROMPTS = {
    "ED Doctor": """
    You are a medical assistant specializing in emergency medicine using the llama3 model.
    Your task is to synthesize the patient's clinical data below into a highly dense, critical clinical summary.
    Focus strictly on life-threatening risks, medication contraindications, allergies, and recent acute changes.

    MANDATORY RESPONSE STRUCTURE:
    1. CRITICAL ALERT / ALLERGIES: (Highlight the most imminent risk)
    2. CURRENT ISSUES: (Concise list of conditions and altered vital signs)
    3. IMMEDIATE ACTION RECOMMENDATION: (Quick actions for the attending physician)
    """,
    
    "Care Manager": """
    You are a nurse or care manager focused on population health coordination and continuity of care.
    Analyze the patient data below focusing on treatment adherence, CarePlan goals, pending appointments, and preventing hospital readmissions.

    MANDATORY RESPONSE STRUCTURE:
    1. MAIN ISSUES AND ADHERENCE: (Focus on chronic disease control and lab tests)
    2. RECENT CHANGES: (Analysis of the latest encounters and prescriptions)
    3. RISKS / FOLLOW-UP ITEMS: (What needs to be scheduled or monitored at home)
    """,
    
    "Patient": """
    You are an empathetic and clear health assistant. Translate the complex medical data below into simple, jargon-free, direct, and welcoming language aimed at the patient, John Doe, himself.

    MANDATORY RESPONSE STRUCTURE:
    1. HOW MY HEALTH IS TODAY: (Explain conditions and tests simply, using metaphors if necessary, like blood sugar)
    2. WHAT CHANGED RECENTLY: (New medications or recent appointments)
    3. MY NEXT STEPS AND CARE: (Allergies to remember and practical daily care)
    """,
    
    "Family Caregiver": """
    You are a health counselor assisting the family member responsible for the patient's daily care.
    Focus on practical management instructions, medication administration, warning signs to seek a hospital, and daily care support.

    MANDATORY RESPONSE STRUCTURE:
    1. IMPORTANT ALERTS AND ALLERGIES: (What the caregiver must never administer or forget)
    2. CURRENT MEDICATION ROUTINE AND CARE: (What needs to be monitored daily)
    3. WARNING SIGNS (When to call the doctor or go to the hospital):
    """
}

st.title("🏥 InterSystems IRIS Health Assistant")

tab1, tab2 = st.tabs(["Smart Patient Summary", "NL to FHIR Query Explorer"])

with tab1:
    st.subheader("Smart Patient Summary Generator")
    st.markdown("AI-assisted generation of clinical summaries based on the **HL7 FHIR** standard and **InterSystems IRIS**.")

    col1, col2 = st.columns(2)
    with col1:
        patient_id = st.text_input("Patient ID (IRIS FHIR)", "1")
    with col2:
        selected_role = st.selectbox("Select the Recipient Role:", list(PERSONA_PROMPTS.keys()))

    if st.button("Generate Smart Summary"):
        with st.spinner("Fetching data from InterSystems IRIS FHIR Server..."):
            raw_fhir_data = fetch_patient_fhir_bundle(patient_id)
            
        if raw_fhir_data:
            st.success("FHIR data loaded successfully!")
            
            clinical_context = json.dumps(raw_fhir_data, indent=2, ensure_ascii=False)
            
            try:
                llm = Ollama(base_url=OLLAMA_URL, model=MODEL_NAME)
                
                system_instruction = PERSONA_PROMPTS[selected_role]
                
                prompt_template = PromptTemplate.from_template(
                    """
                    {system_instruction}
                    
                    CONSOLIDATED PATIENT FHIR DATA:
                    {clinical_context}
                    
                    Please provide the structured summary in English.
                    """
                )
                
                chain = prompt_template | llm | StrOutputParser()
                
                with st.spinner(f"Processing summary with the {MODEL_NAME} model from the perspective of the {selected_role}..."):
                    response_text = chain.invoke({
                        "system_instruction": system_instruction,
                        "clinical_context": clinical_context
                    })
                    
                st.markdown("---")
                st.subheader(f"📋 Custom Summary for: {selected_role}")
                st.markdown(response_text)
                st.subheader("{ } JSON:")
                st.json(raw_fhir_data)
                
            except Exception as e:
                st.error(f"Error processing the request in Ollama/LangChain: {e}")
                st.info("Make sure Ollama is running and the selected model is downloaded (`ollama run llama3`).")
                
        else:
            st.error("Could not retrieve data for the provided patient.")

    
with tab2:
    st.subheader("Natural Language to FHIR Query Explorer")
    st.markdown("Translate natural language questions into structured FHIR queries to discover cohorts and filter patient data.")
    
    nl_query = st.text_input(
        "Ask a question about the patient population:", 
        "List the patients with diabetes"
    )
    
    if st.button("Generate & Execute FHIR Query"):
        try:
            llm = Ollama(base_url=OLLAMA_URL, model=MODEL_NAME)
            
            query_prompt = PromptTemplate.from_template(
                """You are an expert in HL7 FHIR search parameters.
                Translate the following natural language request into a valid FHIR REST API GET query string.
                Only output the relative URL path and query parameters, nothing else. 
                Do not truncate the results.
                
                Example 1: "Find patient named John Smith" -> Patient?given=John&family=Smith
                Example 2: "Find patients with laboratory-confirmed diabetes (using LOINC code 4548-4 for HbA1c >= 6.5%)" -> Patient?_has:Observation:patient:code-value-quantity=http://loinc.org|4548-4$ge6.5
                Example 3: "Find patients with high fasting plasma glucose indicating diabetes (using LOINC code 1558-6 >= 126 mg/dL)" -> Patient?_has:Observation:patient:code-value-quantity=http://loinc.org|1558-6$ge126
                Example 5: "Show female patients" -> Patient?gender=female
                Example 6: "List married patients" -> Patient?marital-status=M
                Example 7: "Patients older than 65" -> Patient?birthdate=le1959-01-01
                Example 8. Find by name (exato/aproximado):
                Example 9: "Find patient named John Smith" -> Patient?given=John&family=Smith
                Example 10: "Search for patient with exact name Silva" -> Patient?name=Silva
                Example 11: "Find patient whose name contains Maria" -> Patient?name:contains=Maria
                Example 12: "Search for patient born on October 23, 1985" -> Patient?birthdate=1985-10-23
                Example 13: "Find patients born before 1990" -> Patient?birthdate=lt1990-01-01
                Example 14: "Search patient by CPF identifier 01234567890" -> Patient?identifier=01234567890
                Example 15: "Search patient by specific system and CPF" -> Patient?identifier=http://saude.gov.br|01234567890
                Example 16: "Find female patients named Silva born on 1990-01-01" -> Patient?name=Silva&gender=female&birthdate=1990-01-01
                Example 17: "Find all male patients" -> Patient?gender=male
                Example 18: "Find patients assigned to practitioner 456" -> Patient?general-practitioner=Practitioner/456
                
                Request: {nl_query}
                
                FHIR Query:"""
            )
            
            chain = query_prompt | llm | StrOutputParser()
            
            with st.spinner(f"Translating query using {MODEL_NAME}..."):
                # Removendo quebras de linha e marcações Markdown caso o LLM adicione por engano
                fhir_query = chain.invoke({"nl_query": nl_query}).replace('\n', '').replace('`', '').strip()
            
            st.info(f"**Generated FHIR Search Query:** `{fhir_query}`")
            
            with st.spinner("Executing query against InterSystems IRIS..."):
                safe_query = fhir_query.lstrip('/')
                query_url = f"{IRIS_FHIR_URL}/{safe_query}"
                
                st.caption(f"**Executing full URL:** `{query_url}`")
                
                auth = (IRIS_USER, IRIS_PASSWORD)
                headers = {"Accept": "application/fhir+json"}
                
                response = requests.get(query_url, headers=headers, auth=auth, timeout=10)
                
                if response.status_code == 200:
                    
                    data = response.json()
                    total = data.get('total', len(data.get('entry', [])))
                    st.success(f"Query successful! Found {total} matching resources.")  

                    prompt_template = PromptTemplate.from_template(
                    """
                    You are a physician specializing in FHIR and must return a textual clinical summary to the following JSON:
                    {data}
                    """)
                
                    # Chain using LCEL (LangChain Expression Language)
                    chain = prompt_template | llm | StrOutputParser()
                    
                    # Execute llama3/Ollama model
                    with st.spinner(f"Processing summary with the {MODEL_NAME} model ..."):
                        response_text = chain.invoke({"data":data})    
                        # Display formatted Result
                        st.markdown("---")
                        st.subheader(f"📋 Summary:")
                        st.markdown(response_text)
                        st.subheader("{ } JSON:")
                        st.json(data)
                else:
                    st.error(f"FHIR Server returned status code {response.status_code}")
                    st.text(response.text)
                    
        except Exception as e:
            st.error(f"Error processing the request: {e}")