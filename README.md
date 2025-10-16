# Speech2TextContainer10

## Docker hosted Azure Speech to text
``` bash
docker rm -f speech-to-text-preview

docker network create speech-net 2>/dev/null || true

docker run -d \
  --name speech-to-text-preview \
  --network speech-net \
  -p 5000:5000 \
  -e EULA=accept \
  -e Billing__SubscriptionKey="$Billing__SubscriptionKey" \
  -e Billing__Region="$Billing__Region" \
  -e Billing="$Billing" \
  -e APIKEY="$APIKEY" \
  -v "$(pwd)/.models:/mnt/models" \
  mcr.microsoft.com/azure-cognitive-services/speechservices/speech-to-text:5.0.3-preview-amd64-en-gb
```

