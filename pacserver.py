#!/usr/bin/env python
"""
Created on Jan 13, 2014

@author: kotaimen
"""

import json

from flask import Flask


with open('config/shadowbroker.json') as fp:
    CONFIG = json.load(fp)

app = Flask(__name__)


@app.route('/shadow.pac')
def shadow():
    ret = '''function FindProxyForURL(url, host)
{
     return "SOCKS %s:%d";
}
''' % (CONFIG['addr'], CONFIG['port'])
    return ret, 200


if __name__ == '__main__':
    print "pac server listens on %s:%d" % (CONFIG['pacserver']['addr'],
                                           CONFIG['pacserver']['port'])

    app.run(host=CONFIG['pacserver']['addr'],
            port=CONFIG['pacserver']['port'])
