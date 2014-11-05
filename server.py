#!/usr/bin/python

import sys
import protocol
from twisted.internet.protocol import Factory
from twisted.internet import ssl, reactor
from twisted.python import log
from OpenSSL import SSL

class ServerContextFactory:
    def getContext(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('/etc/ssl/certs/cert.crt')
        ctx.use_privatekey_file('/etc/ssl/private/priv.key')
        return ctx

class EchoFactory(Factory):
    protocol = protocol.Echo
    connections = 0
    clients = []
    messages = []

if __name__ == '__main__':
    log.startLogging(open('/var/log/chatserver.log', 'a'))
    #log.startLogging(sys.stdout)
    factory = EchoFactory()
    factory.protocol = protocol.Echo
    reactor.listenSSL(443, factory, ServerContextFactory())
    reactor.run()

