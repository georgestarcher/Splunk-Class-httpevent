"""uHEC.py
    MicroPython Splunk HTTP event submission class

    Remember: Friends don't let friends send in non Common Information Model data: http://docs.splunk.com/Documentation/CIM/latest/User/Overview
        Please use CIM friendly field names when sending in data.
"""

import sys

try:
    import json
    import time
except ImportError as err_msg:
    print(err_msg)
    sys.exit(1)

# requests library is required for this class
try:
    import requests
except ImportError:
    try:
        import urequests as requests
    except ImportError as err_msg:
        print(err_msg)
        sys.exit(1)

# setting ntptime is optional for this class
try:
    import ntptime
except ImportError as err_msg:
    print(err_msg)


__author__ = "george@georgestarcher.com (George Starcher)"
http_event_collector_debug = True 

class http_event_collector:

    import sys

    try:
        import json
        import time
        import socket
    except ImportError as err_msg:
        print(err_msg)
        sys.exit(1)

    # requests library is required for this class
    try:
        import requests
    except ImportError:
        try:
            import urequests as requests
        except ImportError as err_msg:
            print(err_msg)
            sys.exit(1)

     # setting ntptime is optional for this class
    try:
        import ntptime
    except ImportError as err_msg:
        print(err_msg)
            
    def __init__(self,token,http_event_server,input_type='json',host="",http_event_port='8088',http_event_server_ssl=True):
        self.token = token
        self.currentByteLength = 0
        self.input_type = input_type

        # Flip to False if you do not want time included in the events sent to Splunk.
        # This will cause time indexed to be the local time of the HEC receiver
        self.includeTime = True 

        # Set host to specified value or default to micropython if no value provided
        if host:
            self.host = host
        else:
            self.host = 'micropython'

        # Build and set server_uri for http event collector
        # Defaults to SSL if flag not passed
        # Defaults to port 8088 if port not passed

        if http_event_server_ssl:
            protocol = 'https'
        else:
            protocol = 'http'

        if input_type == 'raw':
            input_url = '/raw?channel='+str('uuid')
        else:
            input_url = '/event'
            
        self.server_uri = '%s://%s:%s/services/collector%s' % (protocol, http_event_server, http_event_port, input_url)

        if http_event_collector_debug:
            print(self.token)
            print(self.server_uri)
            print(self.input_type)               

    def sendEvent(self,payload,eventtime=""):
        # Method to immediately send an event to the http event collector

        headers = {'Authorization':'Splunk '+self.token}


        if self.input_type == 'json':
            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host":self.host})

            # if self.includeTime is set to True then include the local system timestamp
            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            # Note that epoch for embedded systems do not match epoch for POSIX that Splunk expects. 
            # We adjust for the offset difference.
            # Reference: https://docs.micropython.org/en/latest/pyboard/library/utime.html

            if self.includeTime and not eventtime and 'time' not in payload:
                timeOffsetForEmbeddedEpoch = 946684800 
                eventtime = str(int(time.time()+timeOffsetForEmbeddedEpoch))
                payload.update({"time":eventtime})

            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host":self.host})

        # send event to http event collector
        event = []
        if self.input_type == 'json':
            event.append(json.dumps(payload))
        else:
            event.append(str(payload))

        if http_event_collector_debug:
            print("Single Submit:")
            print(event[0])

        r = requests.post(self.server_uri, data=event[0], headers=headers)
        print(r.text)

        return()

    def set_ntp_time(self):

        try:
            ntptime.settime()
            return(time.time())
        except Exception as err_msg:
            print(err_msg)
            return()

def main():

    # This main method is a test and example section. Normal use you would import this class into your code you wish to send

    # Create event collector object, default SSL and HTTP Event Collector Port
    http_event_collector_key_json = "PUTCOLLECTORKEYHERE"
    http_event_collector_host = "HOSTNAMEOFTHECOLLECTOR"

    testeventJSON = http_event_collector(http_event_collector_key_json, http_event_collector_host)

    # Start event payload and add the metadata information
    payload = {}
    payload.update({"index":"main"})
    payload.update({"sourcetype":"txt"})
    payload.update({"source":"feather"})
    payload.update({"host":"mysterymachine"})

    # Optional set NTP. Do we just trust clock is correct? Do we use a seed time?
    # The class does not force NTP attempt on init. That is left to the programmer to decide.
    testeventJSON.set_ntp_time()

    # If you want to not include timestamp in json payloads force the HEC object to not include time
    # testeventJSON.includeTime = False

    # Add 5 test events
    for i in range(5):
        payload.update({"event":{"action":"success","type":"json","message":"hello world","event_id":i}})
        testeventJSON.sendEvent(payload)

    sys.exit(0)

if __name__ ==  "__main__":

    main()
