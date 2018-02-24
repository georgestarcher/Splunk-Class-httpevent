#Python Class for Sending Events to Splunk HTTP Event Collector

Version/Date: 1.2 2016-10-16

Author: George Starcher (starcher)
Email: george@georgestarcher.com

Thanks to Chandler Newby for getting this into the threaded design.

This code is presented **AS IS** under MIT license.


##Description:

This is a python class file for use with other python scripts to send events to a Splunk http event collector.

##Supported product(s): 

* Splunk v6.3.X+
* Splunk v6.4.X+ for the raw input option

 
##Using this Python Class

###Configuration: Manual

You will need to put this with any other code and import the class as needed.
Instantiate a copy of the http_event_collector object and use to generate and submit payloads as you see in the example main() method.
    
#Notes:

* You can use the sendEvent() method to send data immediately.
* It is more efficient to use the batchEvent() and flushBatch() methods to submit multiple events at once across multiple threads.
* You must call flushBatch() if using batchEvent() or you risk exiting your code before all threads have flushed their data to Splunk.
* There is now an optional input_type when declaring your HEC server. It defaults to the normal JSON event format but adds raw support.
* Added a pop null fields option. Defaults to False to preserve existing class behavior. 
