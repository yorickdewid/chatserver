#!/usr/bin/python

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from model import User, Device 
import json

class Echo(Protocol):
    
    def clientPing(self, data):
        message = [{'error':'false', 'code': 206, 'message':'Pong'}]
        self.transport.write(json.dumps(message) + '\n')

    def clientLastOnline(self, data):
        try:
            username = data['username']
            rdata = {}

            user = User(username)
            user.getUser()

            if user.token:
                message = [{'error':'false', 'code': 226, 'message':'Last online returned'}]
                rdata['last_online'] = unicode(user.lastonline.replace(microsecond=0))
                message[0]['data'] = rdata
                self.transport.write(json.dumps(message) + '\n')
            else:
                message = [{'error':'true', 'code': 405, 'message':'Credentials invalid'}]
                self.transport.write(json.dumps(message) + '\n')
        except KeyError:
            message = [{'error':'true', 'code': 401, 'message':'Not in reference format'}]
            self.transport.write(json.dumps(message) + '\n')

    def clientRegister(self, data):
        try:
            username = data['username']
            password = data['password']
            token = data['token']

            if len(password) != 8:
                message = [{'error':'true', 'code': 405, 'message':'Password invalid'}]
                self.transport.write(json.dumps(message) + '\n')
                return

            if len(token) != 40:
                message = [{'error':'true', 'code': 406, 'message':'Token invalid'}]
                self.transport.write(json.dumps(message) + '\n')
                return

            user = User(username)
            user.token = token
            user.password = password
            user.save()

            message = [{'error':'false', 'code': 241, 'message':'User registered'}]
            self.transport.write(json.dumps(message) + '\n')
        except KeyError:
            message = [{'error':'true', 'code': 401, 'message':'Not in reference format'}]
            self.transport.write(json.dumps(message) + '\n')

    def clientRegisterDevice(self, data):
        try:
            username = data['username']
            device_id = data['device']
            token = data['token']

            user = User(username)
            user.getUser()

            if user.token:
                if user.token == token:
                    device = Device(device_id)
                    device.user = user

                    if 'phone_number' in data:
                        device.phone_number = data['phone_number']

                    device.save()
                    user.addDevice(device)
                    message = [{'error':'false', 'code': 236, 'message':'Device registered'}]
                    self.transport.write(json.dumps(message) + '\n')
                else:
                    message = [{'error':'true', 'code': 405, 'message':'Credentials invalid'}]
                    self.transport.write(json.dumps(message) + '\n')
            else:
                message = [{'error':'true', 'code': 405, 'message':'Credentials invalid'}]
                self.transport.write(json.dumps(message) + '\n')
        except KeyError:
            message = [{'error':'true', 'code': 401, 'message':'Not in reference format'}]
            self.transport.write(json.dumps(message) + '\n')

    def clientGetToken(self, data):
        try:
            username = data['username']
            password = data['password']
            rdata = {}

            user = User(username)
            user.getUser()

            if user.token:
                if user.password == password:
                    message = [{'error':'false', 'code': 246, 'message':'Token returned'}]
                    rdata['token'] = user.token
                    message[0]['data'] = rdata
                    self.transport.write(json.dumps(message) + '\n')
                else:
                    message = [{'error':'true', 'code': 405, 'message':'Credentials invalid'}]
                    self.transport.write(json.dumps(message) + '\n')
            else:
                message = [{'error':'true', 'code': 405, 'message':'Credentials invalid'}]
                self.transport.write(json.dumps(message) + '\n')
        except KeyError:
            message = [{'error':'true', 'code': 401, 'message':'Not in reference format'}]
            self.transport.write(json.dumps(message) + '\n')

    def handle(self, x):
        return {
            205 : self.clientPing,
            240 : self.clientRegister,
            245 : self.clientGetToken,
            225 : self.clientLastOnline,
            235 : self.clientRegisterDevice,
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

            if 'data' in req:
                self.data = req['data']

            self.handle(self.code)(self.data)
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

