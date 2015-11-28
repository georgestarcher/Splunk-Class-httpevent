from splunk_http_event_collector import http_event_collector 
import random
import json

def commitCrime():

    # list of sample values
    suspects = ['Miss Scarett','Professor Plum','Miss Peacock','Mr. Green','Colonel Mustard','Mrs. White']
    weapons = ['candlestick','knife','lead pipe','revolver','rope','wrench']
    rooms = ['kitchen','ballroom','conservatory','dining room','cellar','billiard room','library','lounge','hall','study']

    return {"killer":random.choice(suspects), "weapon":random.choice(weapons), "location":random.choice(rooms), "victim":"Mr Boddy"}

# Create event collector object, default SSL and HTTP Event Collector Port
http_event_collector_key = "B02336E2-EEC2-48FF-9FA8-267B553A0C6B"
http_event_collector_host = "localhost"

testevent = http_event_collector(http_event_collector_key, http_event_collector_host)

# Start event payload and add the metadata information
payload = {}
payload.update({"index":"temp"})
payload.update({"sourcetype":"crime"})
payload.update({"source":"witness"})
payload.update({"host":"mansion"})

# Report 5 Crimes
for i in range(1,5):
    event = commitCrime()
    event.update({"action":"success"})
    event.update({"crime_type":"single"})
    payload.update({"event":event})
    testevent.sendEvent(payload)

# Report 50 Crimes
for i in range(1,50):
    event = commitCrime()
    event.update({"action":"success"})
    event.update({"crime_type":"batch"})
    payload.update({"event":event})
    testevent.batchEvent(payload)
testevent.flushBatch()

