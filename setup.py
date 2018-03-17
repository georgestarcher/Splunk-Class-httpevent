#!/usr/bin/env python

from distutils.core import setup

setup(name='Splunk-HEC',
      version='1.5',
      description='This is a python class file for use with other python scripts to send events to a Splunk http event collector.',
      author='George (starcher) Starcher',
      author_email='george@georgestarcher.com',
      url='https://www.splunk.com/blog/2015/12/11/http-event-collect-a-python-class/',
      project_urls={
          'Source': 'https://github.com/georgestarcher/Splunk-Class-httpevent/blob/master/splunk_http_event_collector.py',
          'Example': 'https://github.com/georgestarcher/Splunk-Class-httpevent/blob/master/example.py',},
      py_modules=['splunk_http_event_collector'],
      keywords="Splunk HEC",
      license="MIT"
     )

