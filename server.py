#!/usr/bin/python

from OpenSSL import SSL

class ServerContextFactory:
    def getContext(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('/etc/ssl/certs/cert.crt')
        ctx.use_privatekey_file('/etc/ssl/private/priv.key')
        return ctx

if __name__ == '__main__':
    import sys
    import protocol
    from twisted.internet.protocol import Factory
    from twisted.internet import ssl, reactor
    from twisted.python import log

    log.startLogging(open('/var/log/chatserver.log', 'a'))
    factory = Factory()
    factory.protocol = protocol.Echo
    factory.clients = []
    factory.chats = []
    reactor.listenSSL(443, factory, ServerContextFactory())
    reactor.run()

