#!/usr/bin/env python

import gevent
import gevent.monkey
gevent.monkey.patch_all()

# import eventlet
# eventlet.monkey_patch()

import json
import socket
import select
import SocketServer
import struct
import logging

import selectproxy

CONFIG = json.load(open('config.json'))


def send_all(sock, data):
    bytes_sent = 0
    while True:
        r = sock.send(data[bytes_sent:])
        if r < 0:
            return r
        bytes_sent += r
        if bytes_sent == len(data):
            return bytes_sent


def lookup_upstream(proxy):
    return (CONFIG['upstreams'][proxy]['addr'], CONFIG['upstreams'][proxy]['port'])

class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):    
    allow_reuse_address = True

class Socks5Handler(SocketServer.StreamRequestHandler):
    
    def handle(self):
        try:
            self.do_handle()
        except socket.error:
            logging.exception('Socket Error')
        except Exception:
            logging.exception('Unexpected Error')
    
    def do_handle(self):
        sock = self.connection
        # 1. Version
        sock.recv(262)
        sock.sendall(b"\x05\x00");
        # 2. Request
        data = self.rfile.read(4)
        mode = ord(data[1])
        addrtype = ord(data[3])
        if addrtype == 1:       # IPv4
            addr = socket.inet_ntoa(self.rfile.read(4))
        elif addrtype == 3:     # Domain name
            addr = self.rfile.read(ord(sock.recv(1)[0]))
        port = struct.unpack('>H', self.rfile.read(2))
        reply = b"\x05\x00\x00\x01"
        try:
            if mode == 1:  # 1. Tcp connect
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                proxy = selectproxy.select_proxy(addr)
                logging.debug('Host "%s" is %s', addr, proxy)
                if proxy in ('LOCAL', 'DOMESTIC'):
                    logging.info('Direct connect to %s:%d', addr, port[0])
                    remote.connect((addr, port[0]))
                    local = remote.getsockname()
                    reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
                else:
                    logging.info('Proxy %s to %s:%d', proxy, addr, port[0])
                    remote.connect(lookup_upstream(proxy))
                    local = remote.getsockname()
                    reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
                    remote.sendall(b"\x05\x01\x00")
                    data = remote.recv(262)
                    if addrtype == 1:
                        tosend = b"\x05\x01\x00\x01" + socket.inet_aton(addr)
                    elif addrtype == 3:
                        tosend = b"\x05\x01\x00\x03"+struct.pack('B', len(addr)) + bytes(addr)
                        tosend += struct.pack('>H', port[0])
                        logging.debug('Sending "%r"' %tosend)
                    remote.sendall(tosend)
                    data = remote.recv(262)
                    logging.debug("Data len: %i", len(data))
 
            else:
                reply = b"\x05\x07\x00\x01" # Command not supported
        except socket.error:
            # Connection refused
            reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'
            
        sock.sendall(reply)
        
        # 3. Transfering
        if reply[1] == '\x00':  # Success
            if mode == 1:    # 1. Tcp connect
                self.do_handle_tcp(sock, remote)

    def do_handle_tcp(self, sock, remote):
        fdset = [sock, remote]
        while True:
            r, w, e = select.select(fdset, [], [])
            if sock in r:
                data = sock.recv(4096)
                if len(data) <= 0:
                    logging.error('Read error from sock')
                    break
                elif send_all(remote, data) < len(data):
                    logging.error('Send error to remote')
                    break
            if remote in r:
                data = remote.recv(4096)
                if len(data) <= 0:
                    logging.error("Read error from remote, len = %i" % len(data))
                    break
                elif send_all(sock, data) < len(data):
                    logging.error("Send error to sock")
                    break                
                
def main():
    logging.basicConfig(level=logging.DEBUG, 
    # filename='socks.log', filemode='a'
    )
    logging.debug('Config %r', CONFIG)
        
    server = TCPServer((CONFIG['addr'], CONFIG['port']), Socks5Handler)
    server.serve_forever()

if __name__ == '__main__':
    main()

