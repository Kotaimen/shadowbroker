Shadow Broker
=============

SOCKS5 Proxy.
Forked from https://github.com/clowwindy/shadowsocks but heavily modified.

Still in progress of rewriting everything.
This is slower than `sshuttle` but ssh tunnel is still most reliable.

Usage
-----

Prerequests (ubuntu):
```
apt-get install python-gevent python-geoip
```

Prerequests (brew):
```
brew install geoip
pip install gevent geoip
```

Clone, run `data/get_geoipdb.sh` to download GeoIP database.

Run ssh using:
```
ssh user@remote -D 127.0.0.1:1081 -g -N
```

Add `-c blowfish` if you don't care safety.

Modify `config.json` as needed , note default listens on `127.0.0.1`.

Run:

```
./shadowbroker.py
```

Tested on ubuntu/mac/pi.

Issues
--------

- No logging/monitoring yet.
- There is a eventlet branch which is runnable using pypy 2.2+, but it runs into "out of socket" error...
