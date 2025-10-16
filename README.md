# Speech2TextContainer10
This is research spike code to validate the capabilities of Azure AI Containers running locally (in prep for running disconnected)   

## Docker hosted Azure Speech to text

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
./workspaces/Speech2TextContainer10/.env && docker run -d \
   --name speech-to-text-preview \
   --network speech-net \
   -p 5000:5000 \
   -e EULA=accept \
   -e Billing__SubscriptionKey="$Billing__SubscriptionKey" \
   -e Billing="$Billing" \
   -e Billing__Region="$Billing__Region" \
   -e APIKEY="$APIKEY" \
   mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb
```

### Run the Transcription Python CLI
```bash
python3 cli/cli_sdk.py --debug docs/assets/voice-sample16.wav
``` 
