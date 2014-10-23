#!/usr/bin/python

from OpenSSL import SSL

class ServerContextFactory:
    def getContext(self):
        """Create an SSL context.
        
        This is a sample implementation that loads a certificate from a file 
        called 'server.pem'."""
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

    log.startLogging(sys.stdout)
    factory = Factory()
    factory.protocol = protocol.Echo
    reactor.listenSSL(443, factory, ServerContextFactory())
    reactor.run()

