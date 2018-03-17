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
http_event_collector_key = "4D14F8D9-D788-4E6E-BF2D-D1A46441242E"
http_event_collector_host = "localhost"

testevent = http_event_collector(http_event_collector_key, http_event_collector_host)
testevent.popNullFields = True

# Start event payload and add the metadata information
payload = {}
payload.update({"index":"test"})
payload.update({"sourcetype":"crime"})
payload.update({"source":"witness"})
payload.update({"host":"mansion"})

# Report 5 Crimes
for i in range(5):
    event = commitCrime()
    event.update({"action":"success"})
    event.update({"crime_type":"single"})
    event.update({"crime_number":i})
    payload.update({"event":event})
    testevent.sendEvent(payload)

# Report 50,000 Crimes
# Do NOT make more than 99,999 events in same timestamp. 
# It will cause Splunk to error on any searches due to more 100K or more events in the index for the same timestamp.

for i in range(50000):
    event = commitCrime()
    event.update({"action":"success"})
    event.update({"crime_type":"batch"})
    event.update({"crime_number":i})
    payload.update({"event":event})
    testevent.batchEvent(payload)
testevent.flushBatch()

# be sure to call flushBatch() before ending your code. Otherwise you risk ending before all threads have flushed.

