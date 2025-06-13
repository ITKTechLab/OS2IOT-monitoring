import requests
import json
import os
from datetime import datetime, timedelta

with open(os.path.dirname(os.path.realpath(__file__)) + "/settings.json") as json_settings_file:
    json_settings = json.load(json_settings_file)

os2iot_url = json_settings['os2iot']['base_url'] + "chirpstack/gateway?organizationId=2"
sms2go_url = "https://pushapi.ecmr.biz/v1.0/Sms/batches/" + json_settings['sms2go']['gatewayid']
textmessage = ""

response = requests.request("GET", os2iot_url, headers={"x-api-key": json_settings['os2iot']['api-key']})

responsejson = json.loads(response.text)

for item in responsejson['resultList']:
  
  if ("silenced_until" in item['tags']):
    silenced_until = datetime.strptime(item['tags']['silenced_until'], "%d-%m-%yT%H:%M:%S")
  else:
    silenced_until = datetime.now() - timedelta(days=1)

  if item['lastSeenAt'] == None: item['lastSeenAt'] = "2000-01-01T00:00:00Z"  # Fallback for devices that have never been seen

  if (item['status'] == "IN-OPERATION") or (item['status'] == "PROJECT"):
    #print(item['status'] + " - " + item['name'])
    timenotseen = datetime.now().astimezone() - datetime.fromisoformat(item['lastSeenAt'].replace('Z', '+00:00'))
    if ((timenotseen.days * 86400 + timenotseen.seconds) > 3600) and (silenced_until < datetime.now()):

      textmessage += item['name'] + ":\r\nLast seen: " + item['lastSeenAt'][0:16] + "\r\n\r\n"
  elif(item['status'] == "OTHER") or (item['status'] == "PROTOTYPE") or (item['status'] == "NONE"):
     #print("- " + item['gatewayId'] + " - " + item['status'])
     pass
  elif item['status'] is None:
    #print (item['gatewayId'] + " - error in metadata\r\n\r\n")
    textmessage += item['gatewayId'] + " - error in metadata\r\n\r\n"
  else:
    print("- " + item['gatewayId'] + " - " + item['status'] + " ----- something is wrong")
    textmessage += item['gatewayId'] + " - error in metadata\r\n\r\n"

textmessage = textmessage[0:750]  # Limit to 1600 characters to avoid SMS2GO API errors

if textmessage != "":
  sms2go_response = requests.request(
    "POST",
      sms2go_url,
      headers={
      "Content-Type": "application/json",
      "Authorization": "Bearer " + json_settings['sms2go']['bearer']
    },
    allow_redirects=True,
    data=json.dumps({
      "body": textmessage.encode(encoding="ASCII", errors="ignore").decode(),
      "to": [json_settings['sms2go']['recipient']]
    }
    )
  )
  if sms2go_response.status_code == 200:
      print(":: SMS sent successfully to " + json_settings['sms2go']['recipient'])
      print(textmessage)
  else:
      print(f":: Failed to send SMS: {sms2go_response.status_code} - {sms2go_response.text}")
else:
  print(":: All gateways are online")
