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

import logging

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
            http_event_port -- Splunk HEC network port (default 8088)
            http_event_server_ssl -- boolean to set if Splunk HEC is using SSL (default True) 

        Attributes:
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
    # Number of threads used to send events to the HEC endpoint (max concurrency).
    # If event batching is used, a single thread may send multiple events at a time in a single http request.
    threadCount = 10
    # Limit the size of the flushQueue, that buffers events for the sending threads.
    maxQueueSize = 100 * threadCount

    # An improved requests retry method from
    # https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    # 503 added for endpoint busy
    # 408 added in case using HAproxy

    def requests_retry_session(self, retries=3,backoff_factor=0.3,status_forcelist=(408,500,502,503,504),session=None):
        session = session or requests.Session()
        retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist, allowed_methods=frozenset(['HEAD', 'TRACE', 'GET', 'PUT', 'OPTIONS', 'DELETE', 'POST']))
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def __init__(self,token,http_event_server,input_type='json',host="",http_event_port='8088',http_event_server_ssl=True):

        self.log = logging.getLogger(u'HEC')
        self.log.setLevel(logging.INFO)

        self.token = token
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
        self.flushQueue = Queue.Queue(maxsize=self.maxQueueSize)
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
     
        self.log.info("HEC Instance Ready: server_uri=%s",self.server_uri)

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

    def check_connectivity(self):
        """
        method to check connectivity to Splunk HEC

        Reference:
            https://docs.splunk.com/Documentation/Splunk/8.0.2/Data/TroubleshootHTTPEventCollector

        Notes:
            method will return true even if HEC token is wrong because system is reachable. 
            method will log warning on reachable errors to show bad token
            method will warn on splunk hec server health codes
        """

        self.log.info("Checking HEC Server URI reachability.")
        headers = {'Authorization':'Splunk '+self.token, 'X-Splunk-Request-Channel':str(uuid.uuid1())}
        payload = dict()
        response = dict() 
        hec_reachable = False
        acceptable_status_codes = [400,401,403]
        heath_warning_status_codes = [500,503]
        try:
            response = self.requests_retry_session().post(self.server_uri, data=payload, headers=headers, verify=self.SSL_verify)
            if response:
                self.log.info("Splunk Server URI is reachable.")
                hec_reachable = True
            else:
                if response.status_code in acceptable_status_codes:
                    self.log.info("Splunk Server URI is reachable.")
                    self.log.warn("Connectivity Check: http_status_code=%s http_message=%s",response.status_code,response.text)
                    hec_reachable = True
                elif response.status_code in heath_warning_status_codes:
                    self.log.warn("Splunk HEC Server has potential health issues")
                    self.log.error("Connectivity Check: http_status_code=%s http_message=%s",response.status_code,response.text)
                else:
                    self.log.warn("Splunk Server URI is unreachable.")
                    self.log.error("HTTP status_code=%s message=%s",response.status_code,response.text)
        except Exception as e:
            self.log.warn("Splunk Server URI is unreachable.")
            self.log.exception(e)

        return (hec_reachable)


    def sendEvent(self,payload,eventtime=""):
        """
        Method to immediately send an event to the http event collector
        
        When the internal queue is exausted, this function _blocks_ until a slot is available.
        """

        if self.input_type == 'json':
            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(round(time.time(),3))
            if eventtime and 'time' not in payload:
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
            event.append(json.dumps(payload, default=str))
        else:
            event.append(str(payload))

        self.flushQueue.put(event)
        self.log.debug("Single Submit: Sticking the event on the queue.")
        self.log.debug("event:%s",event)
        self._waitUntilDone()

    def batchEvent(self,payload,eventtime=""):
        """
        Recommended Method to place the event on the batch queue. Queue will auto flush as needed.

        When the internal queue is exausted, this function _blocks_ until a slot is available.
        """

        if self.input_type == 'json':
            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host":self.host})

            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(round(time.time(),3))
            if eventtime and 'time' not in payload:
                payload.update({'time':eventtime})
            if self.popNullFields:
                payloadEvent = payload.get('event')
                payloadEvent = {k:payloadEvent.get(k) for k,v in payloadEvent.items() if v}
                payload.update({"event":payloadEvent})
            payloadString = json.dumps(payload, default=str)

        else:
            payloadString = str(payload)
            if not payloadString.endswith("\n"):
                payloadString=payloadString+"\n"

        payloadLength = len(payloadString)

        if ((self.currentByteLength+payloadLength) > self.maxByteLength or (self.maxByteLength - self.currentByteLength) < payloadLength):
            self.log.debug("Auto Flush: Sticking the batch on the queue.")
            self.flushQueue.put(self.batchEvents)
            self.batchEvents = []
            self.currentByteLength = 0

        self.batchEvents.append(payloadString)
        self.currentByteLength += payloadLength

    def _batchThread(self):
        """Internal Function: Threads to send batches of events."""
        
        while True:
            self.log.debug("Events received on thread. Sending to Splunk.")
            payload = " ".join(self.flushQueue.get())
            headers = {'Authorization':'Splunk '+self.token, 'X-Splunk-Request-Channel':str(uuid.uuid1())}
            # try to post payload twice then give up and move on
            try:
                response = self.requests_retry_session().post(self.server_uri, data=payload, headers=headers, verify=self.SSL_verify)
                self.log.debug("batch_thread: http_status_code=%s http_message=%s",response.status_code,response.text)
            except Exception as e:
                self.log.exception(e)

            self.flushQueue.task_done()
            
    def _waitUntilDone(self):
        """Internal Function: Block until all flushQueue is empty."""
        self.flushQueue.join()
        return


    def flushBatch(self):
        """Method called to force flushing of remaining batch events.
           Always call this method before exiting your code to send any partial batch queue.
        """

        self.log.debug("Manual Flush: Sticking the batch on the queue.")
        self.flushQueue.put(self.batchEvents)
        self.batchEvents = []
        self.currentByteLength = 0
        self._waitUntilDone()

def main():

    # init logging config, this would be job of your main code using this class.
    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S %z')

    # This main method is a test and example section. Normal use you would import this class into your code you wish to send

    # Create event collector object, default SSL and HTTP Event Collector Port
    http_event_collector_key_json = "PUTCOLLECTORKEYHERE"
    http_event_collector_key_raw = "PUTCOLLECTORKEYHERE"
    http_event_collector_host = "HOSTNAMEOFTHECOLLECTOR"

    # Example with the JSON connection logging to debug
    testeventJSON = http_event_collector(http_event_collector_key_json, http_event_collector_host,'json')
    testeventJSON.log.setLevel(logging.DEBUG)
  
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

    # Batch add 50000 test events
    for i in range(50000):
        payload.update({"event":{"action":"success","type":"json","message":"batch hello world","testBool":"","event_id":i}})
        testeventJSON.batchEvent(payload)
    testeventJSON.flushBatch()

    # Example with the JSON connection logging default to INFO

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
        testeventRAW.sendEvent("%s type=raw message=individual" % time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime()))

    # Batch add 50000 test events
    for i in range(50000):
        payload.update({"event":{"action":"success","type":"json","message":"batch hello world","testBool":"","event_id":i}})
        testeventRAW.batchEvent("%s type=raw message=batch event_id=%s" % (time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime()), str(i)))
    testeventRAW.flushBatch()

    exit()

if __name__ ==  "__main__":

    main()
