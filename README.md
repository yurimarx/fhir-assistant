 [![Gitter](https://img.shields.io/badge/Available%20on-Intersystems%20Open%20Exchange-00b2a9.svg)](https://openexchange.intersystems.com/package/fhir-assistant)
 
# iris-assistant
Clinical summary and natural text agents for FHIR API using Ollama, the LLM lhama3, LangChain, and InterSystems IRIS FHIR Server to:
- Tab 1. Generate clinical summaries from the perspective of the clinician, caregiver, patient, and family member based on the patient ID.
- Tab 2. Transform textual questions into calls to the IRIS FHIR Server API and then analyze the results with the LLM.
- Tab 3. Generate AI charts from Patient Observations data.

## Prerequisites
Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker desktop](https://www.docker.com/products/docker-desktop) installed.

## Installation

### Docker (e.g. for dev purposes)

Clone/git pull the repo into any local directory

```
$ git clone https://github.com/yurimarx/fhir-assistant.git
```

Open the terminal in this directory and run:

```
$ docker-compose build
```


```
$ docker-compose up -d
```

## Agent UI
1. Go to Smart Patient Summary tab type Patient ID (1 to 10) and Role (e.g. ED Doctor) and click Generate Smart Summary button.

<img alt="Image" src="https://github.com/yurimarx/fhir-assistant/blob/master/picture1.png?raw=true"/>

2. See the results:

<img alt="Image" src="https://github.com/yurimarx/fhir-assistant/blob/master/picture2.png?raw=true"/>


3. Go to NL to FHIR Query Explorer and Ask a question about the patient population (e.g: List the patients with diabetes and gender male):

<img alt="Image" src="https://github.com/yurimarx/fhir-assistant/blob/master/picture1.png?raw=true"/>


4. See the results:

<img alt="Image" src="https://github.com/yurimarx/fhir-assistant/blob/master/picture4.png?raw=true"/>


## Patient data
The template goes with 5 preloaded patents in [/data/fhir](https://github.com/intersystems-community/iris-fhir-server-template/tree/master/data/fhir) folder which are being loaded during [docker build](https://github.com/intersystems-community/iris-fhir-server-template/blob/8bd2932b34468f14530a53d3ab5125f9077696bb/iris.script#L26)
You can generate more patients doing the following. Open shel terminal in repository folder and call:
```
#./synthea-loader.sh 10
```
this will create 10 more patients in data/fhir folder.
Then open IRIS terminal in FHIRSERVER namespace with the following command:
```
docker-compose exec iris iris session iris -U FHIRServer
```
and call the loader method:
```
FHIRSERVER>d ##class(fhirtemplate.Setup).LoadPatientData("/data/fhir","FHIRSERVER","/fhir/r4")
```

 with using the [following project](https://github.com/intersystems-community/irisdemo-base-synthea)

## Testing FHIR R4 API

Open URL http://localhost:32783/fhir/r4/metadata
you should see the output of fhir resources on this server

## Swagger UI

You can get the Swagger UI and work with it at:
http://localhost:32783/swagger-ui/index.html

To try it Open /Patient/{id} resource and call for the patient 3.
Here is what you should see:
<img width="1273" alt="Image" src="https://github.com/user-attachments/assets/8dc340cc-e5e4-4bf7-9e16-8169f76e27b6" />

## Testing Postman calls
Get fhir resources metadata
GET call for http://localhost:32783/fhir/r4/metadata
<img width="881" alt="Screenshot 2020-08-07 at 17 42 04" src="https://user-images.githubusercontent.com/2781759/89657453-c7cdac00-d8d5-11ea-8fed-71fa8447cc45.png">


Open Postman and make a GET call for the preloaded Patient:
http://localhost:32783/fhir/r4/Patient/1
<img width="884" alt="Screenshot 2020-08-07 at 17 42 26" src="https://user-images.githubusercontent.com/2781759/89657252-71606d80-d8d5-11ea-957f-041dbceffdc8.png">


## Testing FHIR API calls in simple frontend APP

the very basic frontend app with search and get calls to Patient and Observation FHIR resources could be found here:
http://localhost:32783/fhirUI/FHIRAppDemo.html
or from VSCode ObjectScript menu:
<img width="616" alt="Screenshot 2020-08-07 at 17 34 49" src="https://user-images.githubusercontent.com/2781759/89657546-ea5fc500-d8d5-11ea-97ed-6fbbf84da655.png">

While open the page you will see search result for female anemic patients and graphs a selected patient's hemoglobin values:
<img width="484" alt="Screenshot 2020-08-06 at 18 51 22" src="https://user-images.githubusercontent.com/2781759/89657718-2b57d980-d8d6-11ea-800f-d09dfb48f8bc.png">


## More sophisticated UI

The example of a richer UI around the FHIR data can be observed at:
http://localhost:32783/fhir/portal/patientlist.html

Here is an example screenshot of it:
<img width="1381" alt="Image" src="https://github.com/user-attachments/assets/0aa18442-90ed-495a-9fb0-7ced2f121527" />


## Development Resources
[InterSystems IRIS FHIR Documentation](https://docs.intersystems.com/irisforhealth20203/csp/docbook/Doc.View.cls?KEY=HXFHIR)
[FHIR API](http://hl7.org/fhir/resourcelist.html)
[Developer Community FHIR section](https://community.intersystems.com/tags/fhir)

## What's inside the repository

### Dockerfile

The simplest dockerfile which starts IRIS and imports Installer.cls and then runs the Installer.setup method, which creates IRISAPP Namespace and imports ObjectScript code from /src folder into it.
Use the related docker-compose.yml to easily setup additional parametes like port number and where you map keys and host folders.
Use .env/ file to adjust the dockerfile being used in docker-compose.


### .vscode/settings.json

Settings file to let you immedietly code in VSCode with [VSCode ObjectScript plugin](https://marketplace.visualstudio.com/items?itemName=daimor.vscode-objectscript))

### .vscode/launch.json
Config file if you want to debug with VSCode ObjectScript


## Troubleshooting
**ERROR #5001: Error -28 Creating Directory /usr/irissys/mgr/FHIRSERVER/**
If you see this error it probably means that you ran out of space in docker.
you can clean up it with the following command:
```
docker system prune -f
```
And then start rebuilding image without using cache:
```
docker-compose build --no-cache
```
and start the container with:
```
docker-compose up -d
```

This and other helpful commands you can find in [dev.md](https://github.com/intersystems-community/fhir-assistant/blob/cd7e0111ff94dcac82377a2aa7df0ce5e0571b5a/dev.md)
