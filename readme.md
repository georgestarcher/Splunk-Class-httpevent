# Python Class for Sending Events to Splunk HTTP Event Collector

Version/Date: 1.81 2020-08-15

Author: George Starcher (starcher)
Email: george@georgestarcher.com

Thanks to Chandler Newby for getting this into the threaded design.
Thanks to Paul Miller for the pip support.

This code is presented **AS IS** under MIT license.

## Description:

This is a python class file for use with other python scripts to send events to a Splunk http event collector.

## Supported product(s): 

* Splunk v6.3.X+
* Splunk v6.4.X+ for the raw input option

 
## Using this Python Class

### Configuration: Manual

You will need to put this with any other code and import the class as needed.
Instantiate a copy of the http_event_collector object and use to generate and submit payloads as you see in the example main() method.

### Configuration: With pip

    pip install git+git://github.com/georgestarcher/Splunk-Class-httpevent.git

OR

    pip3 install git+git://github.com/georgestarcher/Splunk-Class-httpevent.git

Once installed you can start python then

    from splunk_http_event_collector import http_event_collector
    help(http_event_collector)

### HEC Collector level index and sourcetype

    hec_server.index = "test"
    hec_server.sourcetype = "syslog"

This works for either RAW or JSON. JSON has the option of the normal existing behavior to override per event by placing in the payload as shown in example.py

### Logging

Logging has been improved to use a proper logger. Note that declaring the basicConfig is the job of your calling code. See main on the class py file for example. Because it is just using a logger you can call the setLevel function on it to the level you wish.
    
# Notes:

* You can use the sendEvent() method to send data immediately.
* It is more efficient to use the batchEvent() and flushBatch() methods to submit multiple events at once across multiple threads.
* You must call flushBatch() if using batchEvent() or you risk exiting your code before all threads have flushed their data to Splunk.
* There is now an optional input_type when declaring your HEC server. It defaults to the normal JSON event format but adds raw support.
* Added a pop null fields option. Defaults to False to preserve existing class behavior. 
* Added a check_connectivity method that is optional. See example.py for use and docstrings on the method for details.

# Change Notes:

* Fixed issue where eventtype on sendEvent and batchEvent was not properly assigned if time field missing from payload.

