#Python Class for Sending Events to Splunk HTTP Event Collector

Version/Date: 1.0.0 2015-11-27

Author: George Starcher (starcher)
Email: george@georgestarcher.com

This code is presented **AS IS** under MIT license.


##Description:

This is a python class file for use with other python scripts to send events to a Splunk http event collector.

##Supported product(s): 

* Splunk v6.3.X

 
##Using this Python Class

###Configuration: Manual

You will need to put this with any other code and import the class as needed.
Instantiate a copy of the http_event_collector object and use to generate and submit payloads as you see in the example main() method.
    
#Notes:

* You can use the sendEvent() method to send data immediately.
* It is more efficient to use the batchEvent() and flushBatch() methods to submit multiple events at once.

