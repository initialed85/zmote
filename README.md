Unofficial zmote.io interface
=======================

This module serves as a Python interface for the [zmote.io](http://zmote.io/) 
IoT gadget- it's basically a USB-powered, WiFI connected IR blaster.

The module was written using the 
[zmote.io API documentation](http://www.zmote.io/apis) and tested against two 
real devices.

----

#### Overview

This module supports the discovery of devices via multicast and interacting
with devices via HTTP or TCP; in all instances communication is directly
with the device (and not via the zmote.io cloud application).

#### To install for use standalone/in your project

pip install zmote

##### To actively discover two devices on your local network

<code>
python -m zmote.discoverer -u 2 -a
</code>  

##### To put a device into learn mode via TCP

<code>
python -m zmote.connector -t tcp -d 192.168.1.1 -c learn
</code>

##### To tell a device to send an IR signal via HTTP
<code>
python -m zmote.connector -t htpp -d 192.168.1.1 -c send -p 1:1,0,36000,1,1,32,32,64,32,32,64,32,3264
</code>

### To install for further development

Prerequisites:
 * [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/])

#### Clone the repo
<code>
git clone https://github.com/initialed85/zmote
cd zmote
</code>

#### Build the virtualenv
<code>
mkvirtualenv zmote
pip install -r requirements-dev.txt
</code>

#### Run the tests
<code>
py.test -v
</code>
