"""splunk_http_event_collector.py
    Splunk HTTP event submission class

    Remember: Friends don't let friends send in non Common Information Model data: http://docs.splunk.com/Documentation/CIM/latest/User/Overview
        Please use CIM friendly field names when sending in data.
"""

__author__ = "george@georgestarcher.com (George Starcher)"

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import json
import time
import socket
import threading
import uuid
import sys

is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as Queue
else:
    import queue as Queue

class http_event_collector:

    """
        Splunk HTTP Event Collector Class

        Keyword Arguments:
            token -- the Splunk HEC token value - required
            http_event_server -- the Splunk Server name or ip. Name must be network resolvable. - required
            input_type -- json or raw HEC type - provided at init (default json)
            host -- value to use as host field for events sent to Splunk (default the local system's hostname) 
            http_event_port -- Splunk HEC network port (default 8080)
            http_event_server_ssl -- boolean to set if Splunk HEC is using SSL (default True) 

        Attributes:
            debug -- debug boolean flag (default false) 
            SSL_verify -- boolean flag to force SSL certificate verification (default false)
            popNullFields -- boolean flag to pop null fields off payload prior to sending to Splunk (default false)
            index -- optional index name for HEC events (default None)
            sourcetype -- optional sourcetype name for HEC events (default None)
            server_uri -- computed property for HEC uri based on HEC type, raw metadata etc.

        Example Init:
            from splunk_http_event_collector import http_event_collector
            testeventJSON = http_event_collector("4D14F8D9-D788-4E6E-BF2D-D1A46441242E","localhost")

            For full usage example: https://github.com/georgestarcher/Splunk-Class-httpevent/blob/master/example.py
     """

    # Default batch max size to match splunk's default limits for max byte
    # See http_input stanza in limits.conf; note in testing I had to limit to 100,000 to avoid http event collector breaking connection
    # Auto flush will occur if next event payload will exceed limit
    maxByteLength = 100000
    threadCount = 10

    # An improved requests retry method from
    # https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    # 503 added for endpoint busy
    # 408 added in case using HAproxy

    def requests_retry_session(self, retries=3,backoff_factor=0.3,status_forcelist=(408,500,502,503,504),session=None):
        session = session or requests.Session()
        retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, method_whitelist=frozenset(['GET', 'POST']))
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def __init__(self,token,http_event_server,input_type='json',host="",http_event_port='8088',http_event_server_ssl=True):
        self.token = token
        self.debug = False
        self.SSL_verify = False
        self.http_event_server = http_event_server
        self.http_event_server_ssl = http_event_server_ssl
        self.http_event_port = http_event_port
        self.index = ""
        self.sourcetype = ""
        self.batchEvents = []
        self.currentByteLength = 0
        self.input_type = input_type
        self.popNullFields = False 
        self.flushQueue = Queue.Queue(0)
        for x in range(self.threadCount):
            t = threading.Thread(target=self._batchThread)
            t.daemon = True
            t.start()
        
        if self.SSL_verify == False:
            requests.packages.urllib3.disable_warnings()
    
        # Set host to specified value or default to localhostname if no value provided
        if host:
            self.host = host
        else:
            self.host = socket.gethostname()

        if self.debug:
            print (self.token)
            print (self.server_uri)
            print (self.input_type)               

    @property
    def server_uri(self):

       # Build and set server_uri for http event collector
        # Defaults to SSL if flag not passed
        # Defaults to port 8088 if port not passed

        if self.http_event_server_ssl:
            protocol = 'https'
        else:
            protocol = 'http'

        if self.input_type == 'raw':
            input_url = '/raw?channel='+str(uuid.uuid1())
            if self.sourcetype: input_url = input_url+'&sourcetype='+self.sourcetype
            if self.index: input_url = input_url+'&index='+self.index
        else:
            input_url = '/event'
            if self.sourcetype or self.index: input_url = input_url+'?'
            if self.sourcetype: input_url = input_url+'sourcetype='+self.sourcetype+"&"
            if self.index: input_url = input_url+'index='+self.index+"&"

        server_uri = '%s://%s:%s/services/collector%s' % (protocol, self.http_event_server, self.http_event_port, input_url)
        return (server_uri)


    def sendEvent(self,payload,eventtime=""):
        """Method to immediately send an event to the http event collector"""

        if self.input_type == 'json':
            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(round(time.time(),3))
                payload.update({'time':eventtime})

            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host":self.host})

        # send event to http event collector
        event = []
        if self.input_type == 'json':
            if self.popNullFields:
                payloadEvent = payload.get('event')
                payloadEvent = {k:payloadEvent.get(k) for k,v in payloadEvent.items() if v}
                payload.update({"event":payloadEvent})
            event.append(json.dumps(payload))
        else:
            event.append(str(payload))

        self.flushQueue.put(event)
        if self.debug:
            print ("Single Submit: Sticking the event on the queue.")
            print (event)
        self._waitUntilDone()

    def batchEvent(self,payload,eventtime=""):
        """
            Recommended Method to place the event on the batch queue. Queue will auto flush as needed.
        """

        if self.input_type == 'json':
            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host":self.host})

            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(round(time.time(),3)) 
                payload.update({"time":eventtime})
            if self.popNullFields:
                payloadEvent = payload.get('event')
                payloadEvent = {k:payloadEvent.get(k) for k,v in payloadEvent.items() if v}
                payload.update({"event":payloadEvent})
            payloadString = json.dumps(payload)

        else:
            payloadString = str(payload)
            if not payloadString.endswith("\n"):
                payloadString=payloadString+"\n"

        payloadLength = len(payloadString)

        if ((self.currentByteLength+payloadLength) > self.maxByteLength or (self.maxByteLength - self.currentByteLength) < payloadLength):
            if self.debug:
                print ("Auto Flush: Sticking the batch on the queue.")
            self.flushQueue.put(self.batchEvents)
            self.batchEvents = []
            self.currentByteLength = 0

        self.batchEvents.append(payloadString)
        self.currentByteLength += payloadLength

    def _batchThread(self):
        """Internal Function: Threads to send batches of events."""
        
        while True:
            if self.debug:
                print ("Events received on thread. Sending to Splunk.")
            payload = " ".join(self.flushQueue.get())
            headers = {'Authorization':'Splunk '+self.token}
            # try to post payload twice then give up and move on
            try:
                r = self.requests_retry_session().post(self.server_uri, data=payload, headers=headers, verify=self.SSL_verify)
            except Exception:
                pass

            if self.debug:
                try:
                    print (r.text)
                except:
                    pass
            self.flushQueue.task_done()
            
    def _waitUntilDone(self):
        """Internal Function: Block until all flushQueue is empty."""
        self.flushQueue.join()
        return


    def flushBatch(self):
        """Method called to force flushing of remaining batch events.
           Always call this method before exiting your code to send any partial batch queue.
        """

        if self.debug:
            print ("Manual Flush: Sticking the batch on the queue.")
        self.flushQueue.put(self.batchEvents)
        self.batchEvents = []
        self.currentByteLength = 0
        self._waitUntilDone()

def main():

    # This main method is a test and example section. Normal use you would import this class into your code you wish to send

    # Create event collector object, default SSL and HTTP Event Collector Port
    http_event_collector_key_json = "PUTCOLLECTORKEYHERE"
    http_event_collector_key_raw = "PUTCOLLECTORKEYHERE"
    http_event_collector_host = "HOSTNAMEOFTHECOLLECTOR"

    # Example with the JSON connection set to debug
    testeventJSON = http_event_collector(http_event_collector_key_json, http_event_collector_host,'json')
    testeventJSON.debug = True 

    testeventRAW = http_event_collector(http_event_collector_key_raw, http_event_collector_host,'raw')

    # Set option to pop empty fields to True, default is False to preserve previous class behavior. Only applies to JSON method
    testeventJSON.popNullFields = True 

    # Start event payload and add the metadata information
    payload = {}
    payload.update({"index":"test"})
    payload.update({"sourcetype":"txt"})
    payload.update({"source":"test"})
    payload.update({"host":"mysterymachine"})

    # Add 5 test events
    for i in range(5):
        payload.update({"event":{"action":"success","type":"json","message":"individual hello world","testBool":False,"event_id":i}})
        testeventJSON.sendEvent(payload)
        testeventRAW.sendEvent("%s type=raw message=individual" % time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime()))

    # Batch add 50000 test events
    for i in range(50000):
        payload.update({"event":{"action":"success","type":"json","message":"batch hello world","testBool":"","event_id":i}})
        testeventJSON.batchEvent(payload)
        testeventRAW.batchEvent("%s type=raw message=batch event_id=%s" % (time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime()), str(i)))
    testeventJSON.flushBatch()
    testeventRAW.flushBatch()

    exit()

if __name__ ==  "__main__":

    main()
