"""splunk_http_event_collector.py
    Splunk HTTP event submission class

    Remember: Friends don't let friends send in non Common Information Model data: http://docs.splunk.com/Documentation/CIM/latest/User/Overview
        Please use CIM friendly field names when sending in data.
"""

import requests
import json
import time
import socket

__author__ = "george@georgestarcher.com (George Starcher)"
http_event_collector_debug = False 
http_event_collector_SSL_verify = False

# Default batch max size to match splunk's default limits for max byte 
# See http_input stanza in limits.conf; note in testing I had to limit to 100,000 to avoid http event collector breaking connection
# Auto flush will occur if next event payload will exceed limit
_max_content_bytes = 100000 

class http_event_collector:

    def __init__(self,token,http_event_server,host="",http_event_port='8088',http_event_server_ssl=True,max_bytes=_max_content_bytes):
        self.token = token
        self.batchEvents = []
        self.maxByteLength = max_bytes
        self.currentByteLength = 0
    
        # Set host to specified value or default to localhostname if no value provided
        if host:
            self.host = host
        else:
            self.host = socket.gethostname()

        # Build and set server_uri for http event collector
        # Defaults to SSL if flag not passed
        # Defaults to port 8088 if port not passed

        if http_event_server_ssl:
            buildURI = ['https://']
        else:
            buildURI = ['http://']
        for i in [http_event_server,':',http_event_port,'/services/collector/event']:
            buildURI.append(i)
        self.server_uri = "".join(buildURI)

        if http_event_collector_debug:
            print self.token
            print self.server_uri                

    def sendEvent(self,payload,eventtime=""):
        # Method to immediately send an event to the http event collector

        headers = {'Authorization':'Splunk '+self.token}

        # If eventtime in epoch not passed as optional argument use current system time in epoch
        if not eventtime:
            eventtime = str(int(time.time()))

        # Fill in local hostname if not manually populated
        if 'host' not in payload:
            payload.update({"host":self.host})

        # Update time value on payload if need to use system time
        data = {"time":eventtime}
        data.update(payload)

        # send event to http event collector
        r = requests.post(self.server_uri, data=json.dumps(data), headers=headers, verify=http_event_collector_SSL_verify)

        # Print debug info if flag set
        if http_event_collector_debug:
            print (r.text)
            print data

    def batchEvent(self,payload,eventtime=""):
        # Method to store the event in a batch to flush later

        # Fill in local hostname if not manually populated
        if 'host' not in payload:
            payload.update({"host":self.host})

        payloadLength = len(json.dumps(payload))

        if (self.currentByteLength+payloadLength) > self.maxByteLength:
            self.flushBatch()
            # Print debug info if flag set
            if http_event_collector_debug:
                print "auto flushing"
        else:
            self.currentByteLength=self.currentByteLength+payloadLength

        # If eventtime in epoch not passed as optional argument use current system time in epoch
        if not eventtime:
            eventtime = str(int(time.time()))

        # Update time value on payload if need to use system time
        data = {"time":eventtime}
        data.update(payload)

        self.batchEvents.append(json.dumps(data))

    def flushBatch(self):
        # Method to flush the batch list of events

        if len(self.batchEvents) > 0:
            headers = {'Authorization':'Splunk '+self.token}
            r = requests.post(self.server_uri, data=" ".join(self.batchEvents), headers=headers, verify=http_event_collector_SSL_verify)
            self.batchEvents = []
            self.currentByteLength = 0

def main():

    # This main method is a test and example section. Normal use you would import this class into your code you wish to send

    # Create event collector object, default SSL and HTTP Event Collector Port
    http_event_collector_key = "PUTCOLLECTORKEYHERE"
    http_event_collector_host = "HOSTNAMEOFTHECOLLECTOR"
 
    testevent = http_event_collector(http_event_collector_key, http_event_collector_host)

    # Start event payload and add the metadata information
    payload = {}
    payload.update({"index":"temp"})
    payload.update({"sourcetype":"txt"})
    payload.update({"source":"test"})
    payload.update({"host":"mysterymachine"})

    # Add 5 test events
    for i in range(1,5):
        payload.update({"event":{"action":"success","message":"individual hello world","event_id":i}})
        testevent.sendEvent(payload)

    # Batch add 5 test events
    for i in range(1,500000):
        payload.update({"event":{"action":"success","message":"batch hello world","event_id":i}})
        testevent.batchEvent(payload)
    testevent.flushBatch()

    exit()

if __name__ ==  "__main__":

    main()

