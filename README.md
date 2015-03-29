Shadow Broker
=============

A SOCKS5 proxy which selects backend according to predefined blacklists or 
GeoIP.

Install
-------

Install binary dependency:
    
    apt-get install geoip gevent

Clone the source, run:

    pip install -rrequirements.txt

Go into `data` directory and run:

    ./download_data.sh

This downloads the GeoIP database and gfw list.
   

Setup
-----

Shadowbroker requires a "oversea" socks5 proxy up and running, the easiest is 
use ssh:

    ssh user@remote -D 127.0.0.1:1081 -g -N

Add `-c blowfish` if you don't care safety, use `autossh` for stable 
connections.

Then run shadowbroker:

    ./shadowbroker.py
    
Point browser proxy to `1080` port

Tested on ubuntu/mac/pi.
