#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import socket
import logging
import json

import GeoIP

# ===============================================================================
# Read data
# ===============================================================================

# GeoIP2 seems doesn't work
# Get GeoIP from
# http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
GEOIP_DB = GeoIP.open('data/GeoIP.dat', GeoIP.GEOIP_MEMORY_CACHE)


def parse_gfwlist():
    gfwlist = open('data/gfwlist.txt').read()
    gfwlist = gfwlist.decode('base64')
    for line in gfwlist:
        if line.find('.*') >= 0:
            continue
        elif line.find('*') >= 0:
            line = line.replace('*', '/')
        if line.startswith('||'):
            line = line.lstrip('||')
        elif line.startswith('|'):
            line = line.lstrip('|')
        elif line.startswith('.'):
            line = line.lstrip('.')
        if line.startswith('!'):
            continue
        elif line.startswith('['):
            continue
        elif line.startswith('@'):
            # ignore white list
            continue
        if '/' in line or '%' in line or ':' in line:
            continue
        line = line.strip()
        if line:
            yield line


with open('data/ip_blacklist.txt') as fp:
    BLACKLIST_IP = frozenset(line.strip() for line in fp if line.strip())

with open('data/domain_blacklist.txt') as fp:
    BLACKLIST_DOMAIN = list(line.strip() for line in fp if line.strip())

BLACKLIST_DOMAIN.extend(parse_gfwlist())
BLACKLIST_DOMAIN = frozenset(BLACKLIST_DOMAIN)

with open('data/domain_whitelist.txt') as fp:
    WHITELIST_DOMAIN = frozenset(line.strip() for line in fp if line.strip())

# ===============================================================================
# Magic variables
# ===============================================================================


def ip2int(ip):
    return reduce(lambda x, y: x * 256 + y, map(int, ip.split('.')))


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


# ===============================================================================
# Proxy Selector
# ===============================================================================


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
    print get_geo_ip('4.4.4.4')
    print get_geo_ip('173.194.127.165')
