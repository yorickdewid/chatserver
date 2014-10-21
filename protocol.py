#!/usr/bin/python

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json

class Echo(Protocol):
    
    def clientPing(self):
        message = [{'error':'false', 'code': 206, 'message':'Pong'}]
        self.transport.write(json.dumps(message) + '\n')

    def handle(self, x):
        return {
            205 : self.clientPing,
        }[x]

    def __init__(self):
        self.error = []
        self.code = 100
        self.message = []
        self.data = []

    def dataReceived(self, data):
        try:        
            req = json.loads(data.rstrip())[0]
            self.code = req['code']
            self.error = req['error']
            self.message = req['message']

            print self.code
            self.handle(self.code)()
        except ValueError:
            message = [{'error':'true', 'code': 400, 'message':'Send data in JSON'}]
            self.transport.write(json.dumps(message) + '\n')
        except KeyError:
            message = [{'error':'true', 'code': 401, 'message':'Not in reference format'}]
            self.transport.write(json.dumps(message) + '\n')

    def connectionMade(self):
        message = [{'error':'false', 'code': 200, 'message':'Server ready'}]
        self.transport.write(json.dumps(message) + '\n')
        print 'connected'

    def connectionLost(self, reason):
        print 'disconnected'

