#!/usr/bin/python

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json

class Echo(Protocol):

    def dataReceived(self, data):
#        self.transport.write(data)
        print data.rstrip()

    def connectionMade(self):
        message = [{'error':'false', 'code': 200, 'message':'Server ready'}]
        self.transport.write(json.dumps(message) + '\n')
        print 'connected'

    def connectionLost(self, reason):
        print 'disconnected'\

