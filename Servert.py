from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
import protocol

class proFactory(Factory):
    def buildProtocol(self, addr):
        return protocol()

# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(proFactory())
reactor.run()
