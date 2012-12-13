#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    Author:  Xiaoxia
    Contact: xiaoxia@xiaoxia.org
    Website: xiaoxia.org

    可以使用的代理服务器地址如下：
    电信部分：
        h0.ctc.bj.ie.sogou.com
        h1.ctc.bj.ie.sogou.com
        h2.ctc.bj.ie.sogou.com
        h3.ctc.bj.ie.sogou.com

    联通部分：
        h0.ctc.bj.ie.sogou.com
        h1.ctc.bj.ie.sogou.com
        h2.ctc.bj.ie.sogou.com
        h3.ctc.bj.ie.sogou.com

    教育网部分：
        h0.edu.bj.ie.sogou.com
        h1.edu.bj.ie.sogou.com
        h2.edu.bj.ie.sogou.com
        h3.edu.bj.ie.sogou.com
        h4.edu.bj.ie.sogou.com
        h5.edu.bj.ie.sogou.com
        h6.edu.bj.ie.sogou.com
        h7.edu.bj.ie.sogou.com
        h8.edu.bj.ie.sogou.com
        h9.edu.bj.ie.sogou.com
        h10.edu.bj.ie.sogou.com
        h11.edu.bj.ie.sogou.com
        h12.edu.bj.ie.sogou.com
        h13.edu.bj.ie.sogou.com
        h14.edu.bj.ie.sogou.com
        h15.edu.bj.ie.sogou.com
'''

from threading import Thread
from struct import unpack
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from httplib import HTTPResponse
from SocketServer import ThreadingMixIn
import socket
import time, os, sys, random, re, ConfigParser

print 'Sogou Proxy'
print
print 'Original source codes from:'
print 'http://xiaoxia.org/2011/03/26/using-python-to-write-a-local-sogou-proxy-server-procedures/'
print 'http://blog.csdn.net/tooktang/article/details/6827982'

x_sogou_auth = '9CD285F1E7ADB0BD403C22AD1D545F40/30/853edc6d49ba4e27'
proxy_host = 'h0.cnc.bj.ie.sogou.com'
proxy_port = 80

def calc_sogou_hash(t, host):
    s = (t + host + 'SogouExplorerProxy').encode('ascii')
    code = len(s)
    dwords = int(len(s)/4)
    rest = len(s) % 4
    v = unpack(str(dwords) + 'i'+str(rest)+'s', s)
    for vv in v:
        if(type(vv)==type('i')):
            break
        a = (vv & 0xFFFF)
        b = (vv >> 16)
        code += a
        code = code ^ (((code<<5)^b) << 0xb)
        # To avoid overflows
        code &= 0xffffffff
        code += code >> 0xb
    if rest == 3:
        code += ord(s[len(s)-2]) * 256 + ord(s[len(s)-3])
        code = code ^ ((code ^ (ord(s[len(s)-1])*4)) << 0x10)
        code &= 0xffffffff
        code += code >> 0xb
    elif rest == 2:
        code += ord(s[len(s)-1]) * 256 + ord(s[len(s)-2])
        code ^= code << 0xb
        code &= 0xffffffff
        code += code >> 0x11
    elif rest == 1:
        code += ord(s[len(s)-1])
        code ^= code << 0xa
        code &= 0xffffffff
        code += code >> 0x1
    code ^= code * 8
    code &= 0xffffffff
    code += code >> 5
    code ^= code << 4
    code = code & 0xffffffff
    code += code >> 0x11
    code ^= code << 0x19
    code = code & 0xffffffff
    code += code >> 6
    code = code & 0xffffffff
    return hex(code)[2:].rstrip('L').zfill(8)

class Handler(BaseHTTPRequestHandler):
    s = 0
    def do_proxy(self):
        try:
            if self.s == 0:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((proxy_host, proxy_port))
            self.s.send(self.requestline.encode('ascii') + b'\r\n')
            # Add Sogou Verification Tags
            self.headers['X-Sogou-Auth'] = x_sogou_auth
            t = hex(int(time.time()))[2:].rstrip('L').zfill(8)
            self.headers['X-Sogou-Tag'] = calc_sogou_hash(t, self.headers['Host'])
            self.headers['X-Sogou-Timestamp'] = t
            self.s.send(str(self.headers).encode('ascii') + b'\r\n')
            # Send Post data
            if(self.command=='POST'):
                self.s.send(self.rfile.read(int(self.headers['Content-Length'])))
            response = HTTPResponse(self.s, method=self.command, buffering=True)
            response.begin()
            # Reply to the browser
            status = 'HTTP/1.1 ' + str(response.status) + ' ' + response.reason
            self.wfile.write(status.encode('ascii') + b'\r\n')
            h = ''
            for hh, vv in response.getheaders():
                if hh.upper()!='TRANSFER-ENCODING':
                    h += hh + ': ' + vv + '\r\n'
            self.wfile.write(h.encode('ascii') + b'\r\n')
            while True:
                response_data = response.read(8192)
                if(len(response_data) == 0):
                    break
                self.wfile.write(response_data)
        except socket.error:
            print('socket error for ' + self.requestline)
    def do_POST(self):
        self.do_proxy()
    def do_GET(self):
        self.do_proxy()

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')

CONFIG = ConfigParser.ConfigParser()
CONFIG.read(os.path.splitext(__file__)[0] + '.ini')

listen_ip = CONFIG.get('listen', 'ip')
listen_port = CONFIG.getint('listen', 'port')

server = ThreadingHTTPServer((listen_ip, listen_port), Handler)

print(u'Please select your network environment:\n\
      1. CERNET \n\
      2. CTCNET \n\
      3. CNCNET \n\
      4. DXT    \n\
      Default is CERNET: \n')
i = raw_input()
if i == '1':
    proxy_host = 'h' + str(random.randint(0,10)) + '.edu.bj.ie.sogou.com'
elif i == '2':
    proxy_host = 'h' + str(random.randint(0,3)) + '.ctc.bj.ie.sogou.com'
elif i == '3':
    proxy_host = 'h' + str(random.randint(0,3)) + '.cnc.bj.ie.sogou.com'
elif i == '4':
    proxy_host = 'h' + str(random.randint(0,10)) + '.dxt.bj.ie.sogou.com'
elif len(i) == 0:
    proxy_host = 'h' + str(random.randint(0,10)) + '.edu.bj.ie.sogou.com'

print('Proxy is running on ' + proxy_host + '. Please change your browser\'s proxy to ' + listen_ip + ':' + str(listen_port))
server.serve_forever()