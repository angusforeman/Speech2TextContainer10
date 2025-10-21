# Speech2TextContainer1.0
This is research spike code to validate the capabilities of Azure AI Containers running locally (in prep for running disconnected). 

The Current Implementation supports 
- Speech to Text using 5.0.3  (mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb)   
- Needs Speech SDK to perform Translation (REST interfaces not supported)
-  Spec Kit used accelerate the planning and implementation
- ./docs/techstack.md lists additional tech details

## Sample of Docker hosted Azure Speech to text called from CLI

### Setup docker network (with errors hidden by pipig to null)
```bash
docker network create speech-net 2>/dev/null || true
```
### Remove an existing instance 
``` bash
docker rm -f speech-to-text-preview
```
### Start the local instance of the Azure AI Container
```bash
docker run -d \
   --name speech-to-text-preview \
   --network speech-net \
   -p 5000:5000 \
   -e EULA=accept \
   -e Billing__SubscriptionKey="$Billing__SubscriptionKey" \
   -e Billing="$Billing" \
   -e Billing__Region="$Billing__Region" \
   -e APIKEY="$APIKEY" \
   mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-us
```

### Run the Transcription Python CLI
```bash
set -a && source .env && set +a #set the env vars
python3 cli/s2t_cli_sdk.py --debug docs/assets/voice-sample16.wav
python3 cli/s2t_cli_sdk.py --diarize ./docs/assets/katiesteve.wav #this fails at present due to lack of container immplementation conversation transcriber
python3 cli/s2t_cli_sdk.py --diarize --cloud ./docs/assets/katiesteve.wav 
``` 
# Spec Kit details

## Spec Kit Notes
- Validate that the research phase clarly states Speech SDK 
- Validate that the details in the link provided on container implementation are represented
- Ensure that the implementation code (esp SDK initialisation)  doesnt default back to Cloud rather than container    

## Constitution
update the constitution to reflect the following principles
  Minimal dependencies except when required
  Keep code concise and don’t add additional scope or complexity except when specified 
  This is a research spike, so no need for security or comprehensive testing
  Perform explicit checks to provide the developer with proof of the integrity of the environment or app at key points before proceeding
Build the minimal number of test cases to prove that the relevant part of stack works - one test for each technical element of the solution. 
## Specify
Speech2Texttranscript: I want to be able to utilise  preview version 5.0.3 of the Azure Speech to Text (English) translation service with the service running in its containerised speech to text mode on my local docker environment. I want to be able to demonstrate the functionality by using a simple command line experience that calls the transcription capability in the containerised azure speech service against a supplied audio file that contains multiple speakers and several topics (like meeting audio). The results should be shown on screen. 
## Plan
Assume a DevContainers development environment and create a dockerfile to represent any PostCommand installation requirements and update the devcontainer.JSON to ensure that a devconatiner rebuild will result in the correct environment 
Add an implementation step that creates a shell script called validate_env.sh that checks 100% of all needed backend and frontend packages and relevant permissions are in place. 
Use the Azure Speech SDK not the REST endpoints for the Transcriptiopn service
In validate_env.sh a mechanism to ensure the Azure Speech container image is functioning correctly
Do not use Python virtual envs as we are using devcontainer 
Use /docs/techstack.md as the tech spec for both the CLI and the Speech 2 text container and the related configuration
Assume that a .env file is provided with relevant Azure details
Reference the following re using the Azure speech services in a  container, especially the authentication method https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-container-stt?tabs=disconnected&pivots=programming-language-csharp#run-the-container-with-docker-run 
The container should be available in a locker docker and the docker image details are in /.Readme.md
