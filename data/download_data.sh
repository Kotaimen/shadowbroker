#!/usr/bin/env bash
curl http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz | gunzip > GeoIP.dat
curl https://raw.githubusercontent.com/calfzhou/autoproxy-gfwlist/trunk/gfwlist.txt > gfwlist.txt
