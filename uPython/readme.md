#MicroPython Class for Sending Events to Splunk HTTP Event Collector

Version/Date: 1.0 2017-02-12

Author: George Starcher (starcher)
Email: george@georgestarcher.com

This code is presented **AS IS** under MIT license.


##Description:

This is a MicroPython class file for use with other python scripts to send events to a Splunk http event collector.

##Supported product(s): 

* Splunk v6.3.X+
 
##Using this Python Class

###Configuration: Manual

You will need to put this with any other code and import the class as needed.
Instantiate a copy of the http_event_collector object and use to generate and submit payloads as you see in the example main() method.

Something like from uHEC import http_event_collector should do it.
    
#Notes:

* I have mostly removed references to RAW HEC input code. This is because the uuid library in MicroPython is not suitable at this time. I left the stubs of the code in case I get motivated to work out my own uuid generator that HEC RAW requires.
* The batch support has been removed to avoid having to deal with the small memory limitations in most MicroPython embedded devices.
* This code was tested with the Adafruit Feather Huzzah converted to run MicroPython. <3 Adafrauit!!!!
* The code expects you are handling joining your device to a network with visibility to your Splunk HEC collector.
* The code provides a method to set your device's time via NTP. See the main section example code.
* YOU are responsible for getting the clock right or using the flag to flip off including time in the HEC events so your HEC collector can default to using its own timestamp. After all Splunk is about time series data. Wrong time and your searching won't go well.

* If you are new to devices like the Adafruit Feather Huzzah, go watch Tony D's MicroPython playlist on the Adafruit YouTube channel.

 

