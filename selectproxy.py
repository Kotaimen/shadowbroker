#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import socket
import logging

# brew install libgeoip && pip install GeoIP
import GeoIP

##
# Magic variables
##

# http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
GEOIP_DB = GeoIP.open('GeoIP.dat', GeoIP.GEOIP_MEMORY_CACHE)

BLACKLIST_IP = frozenset(['60.191.124.236', '180.168.41.175', '93.46.8.89',
'203.98.7.65', '8.7.198.45', '78.16.49.15', '46.82.174.68', '243.185.187.39',
'243.185.187.30', '159.106.121.75', '37.61.54.158', '59.24.3.173',
])

BLACKLIST_DOMAIN = frozenset(['skype.com', 'youtube.com'])

WHITELIST_DOMAIN = frozenset(['local', 'localhost'])


def ip2int(ip):
    return reduce(lambda x,y: x * 256 + y, map(int, ip.split('.')))
    
def is_ip_local(ip):
    ip = ip2int(ip)
    ip >>= 16
    if ip == 0xc0a8: 
        # 192.168.0.0~192.168.255.255
        return True
    ip >>= 4
    if ip == 0xac1: 
        # 172.16.0.0~172.31.255.255
        return True
    ip >>= 4
    if ip == 0x7f or ip == 0xa: 
        # 127.0.0.0~127.255.255.255/10.0.0.0~10.255.255.255
        return True
    
    return False
    
def is_ip_gfwed(ip):    
    return ip in BLACKLIST_IP
    
def get_geo_ip(ip):    
    try:
        return GEOIP_DB.country_code_by_addr(ip)
    except Exception:
        return 'UNKNOWN'
    
    
def is_host_local(host):
    return host in WHITELIST_DOMAIN
    
def is_host_gfwed(host):
    return host in BLACKLIST_DOMAIN


def select_proxy(host):
    """ Decide which proxy to use for given hostname.
    Returns: LOCAL/DOMESTIC/OVERSEA
    """
    
    if is_host_local(host):
        return 'LOCAL'        
    elif is_host_gfwed(host):
        return 'OVERSEA'

    try:
        ip = socket.gethostbyname(host)
    except Exception:
        logging.exception('host "%s" not resolved', host)
        return 'LOCAL'
    
    if is_ip_local(ip):
        return 'LOCAL'        
    elif is_ip_gfwed(ip):
        return 'OVERSEA'

    country = get_geo_ip(ip)
    if country == 'UNKNOWN':
        logging.error('unknown geoip for "%s"', ip)        
        return 'LOCAL'
    
    if country == 'CN':
        return 'DOMESTIC'
    else:
        return 'OVERSEA'

if __name__ == '__main__':
    print get_geo_ip('173.194.127.165')