
#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()
from eventlet.green import socket
from eventlet.green import select

import struct
import logging
import contextlib
import json

import selectproxy

#===============================================================================
# Config
#===============================================================================

CONFIG = json.load(open('config.json'))


def lookup_upstream(proxy):
    return (CONFIG['upstreams'][proxy]['addr'],
            CONFIG['upstreams'][proxy]['port'])

#===============================================================================
# SOCKS5 Handler
#===============================================================================


def send_all(sock, data):
    bytes_sent = 0
    while True:
        r = sock.send(data[bytes_sent:])
        if r < 0:
            return r
        bytes_sent += r
        if bytes_sent == len(data):
            return bytes_sent


def handle_socks5(sock, address):
    with contextlib.closing(sock):
        rfile = sock.makefile('r')

        # === Handshake
        sock.recv(262)  # XXX: why 262?
        sock.sendall(b'\x05\x00')  # SOCKS5, no auth
        data = rfile.read(4)
        command = ord(data[1])

        addrtype = ord(data[3])
        if addrtype == 1:  # IPv4
            addr = socket.inet_ntoa(rfile.read(4))
        elif addrtype == 3:  # Domain name
            addr = rfile.read(ord(sock.recv(1)[0]))
        port = struct.unpack('>H', rfile.read(2))

        if command != 1:
            reply = b"\x05\x07\x00\x01"  # Command not supported
            sock.sendall(reply)
            logging.error('Only supports SOCKS no auth')
            return

        reply = b"\x05\x00\x00\x01"
        logging.info('Accepted %r ==> %s:%d', address, addr, port[0],)

        # ==== Connecting
        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            proxy = selectproxy.select_proxy(addr)
            logging.debug('Connecting to "%s" via "%s"', addr, proxy)

            if proxy in ('LOCAL', 'DOMESTIC'):
                # Local connection
                remote.connect((addr, port[0]))
                local = remote.getsockname()
                logging.info('Direct connect %r ==> %s%r ==> %s:%d', address, proxy, local, addr, port[0])
                reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
            else:
                # Upstream SOCKS5
                remote.connect(lookup_upstream(proxy))
                local = remote.getsockname()
                logging.info('Proxy connect %r ==> %s%r ==> %s:%d', address, proxy, local, addr, port[0])
                reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
                remote.sendall(b"\x05\x01\x00")
                data = remote.recv(262)
                if addrtype == 1:
                    tosend = b"\x05\x01\x00\x01" + socket.inet_aton(addr)
                elif addrtype == 3:
                    tosend = b"\x05\x01\x00\x03" + struct.pack('B', len(addr)) + bytes(addr)
                    tosend += struct.pack('>H', port[0])
                    # logging.debug('Sending "%r"' % tosend)
                remote.sendall(tosend)
                data = remote.recv(262)
                # logging.debug("# len: %i", len(data))
        except socket.error:
            # Connection refused
            reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'

        sock.sendall(reply)

        # ==== Transfering
        if reply[1] != '\x00' or command != 1:
            remote.close()
            return

        with contextlib.closing(remote):

            total_sent, total_read = 0, 0
            while True:
                rlist, _wlist, _xlist = select.select([sock, remote], [], [])
                if sock in rlist:
                    data = sock.recv(4096)  # XXX: inefficient... use recv_into?
                    if not data:
                        break
                    sent = send_all(remote, data)
                    total_sent += sent
                    if sent < len(data):
                        break
                if remote in rlist:
                    data = remote.recv(4096)
                    if not data:
                        break
                    read = send_all(sock, data)
                    total_read += read
                    if read < len(data):
                        break
            logging.info('Connection closed, %d bytes read, %d bytes sent', total_read, total_sent)


def main():
    logging.info(CONFIG)
    server = eventlet.listen((CONFIG['addr'], CONFIG['port']))
    pool = eventlet.GreenPool(100)

    while True:
        new_sock, address = server.accept()
        pool.spawn_n(handle_socks5, new_sock, address)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
