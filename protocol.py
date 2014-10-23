#!/usr/bin/python

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from model import User, Device 
import json

class Echo(Protocol):

    def sendAPI(self, error, code, message, data = None):
        api = {}
        api['error'] = error
        api['code'] = code
        api['message'] = message

        if data:
            api['data'] = data

        self.transport.write(json.dumps([api]) + '\n')
 
    def clientPing(self, data):
        self.sendAPI(0,206,'Pong')

    def clientLastOnline(self, data):
        try:
            username = data['username']
            rdata = {}

            user = User(username)
            user.getUser()

            if user.token:
                rdata['last_online'] = unicode(user.lastonline.replace(microsecond=0))
                self.sendAPI(0,226,'Last online returned',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def clientRegister(self, data):
        try:
            username = data['username']
            password = data['password']
            token = data['token']

            if len(password) != 8:
                self.sendAPI(1,405,'Password invalid')
                return

            if len(token) != 40:
                self.sendAPI(1,406,'Token invalid')
                return

            user = User(username)
            user.token = token
            user.password = password
            user.save()

            self.sendAPI(0,241,'User registered')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def clientRegisterDevice(self, data):
        try:
            username = data['username']
            device_id = data['device']
            token = data['token']

            user = User(username)
            user.getUser()

            if user.token: #TODO
                if user.token == token:
                    device = Device(device_id)
                    device.user = user

                    if 'phone_number' in data:
                        device.phone_number = data['phone_number']

                    device.save()
                    user.addDevice(device)

                    self.sendAPI(0,236,'Device registered')
                else:
                    self.sendAPI(1,405,'Credentials invalid')
            else:
                self.sendAPI(1,405,'Credentials invalid')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def clientGetToken(self, data):
        try:
            username = data['username']
            password = data['password']
            rdata = {}

            user = User(username)
            user.getUser()

            if user.token: #TODO
                if user.password == password:
                    rdata['token'] = user.token
                    self.sendAPI(0,246,'Token returned',rdata)
                else:
                    self.sendAPI(1,405,'Credentials invalid')
            else:
                self.sendAPI(1,405,'Credentials invalid')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def clientGetContactList(self, data):
        try:
            username = data['username']
            token = data['token']
            rdata = {}
            rcontacts = []

            user = User(username)
            user.getUser()

            if user.token: #TODO
                if user.token == token: #TODO
                    if 'contacts' in data:
                        for contact in data['contacts']:
                            contactuser = User(contact['contact'])
                            contactuser.getUser()

                            if contactuser.token: #TODO
                                user.addContact(contactuser)

                    for contact in user.getContactList():
                        rcontacts.append({'contact':contact.name})

                    if len(rcontacts):
                        rdata['contacts'] = rcontacts
                        self.sendAPI(0,211,'Contact list send',rdata)
                    else:
                        self.sendAPI(0,211,'Contact list send')
                else:
                    self.sendAPI(1,405,'Credentials invalid')
            else:
                self.sendAPI(1,405,'Credentials invalid')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def handle(self, x):
        return {
            205 : self.clientPing,
            240 : self.clientRegister,
            245 : self.clientGetToken,
            225 : self.clientLastOnline,
            235 : self.clientRegisterDevice,
            210 : self.clientGetContactList
        }[x]

    def dataReceived(self, data):
        try:        
            req = json.loads(data.rstrip())[0]
            code = req['code']
            error = req['error'] #TODO not used at the moment
            message = req['message'] #TODO not used at the moment

            if 'data' in req:
                data = req['data']

            self.handle(code)(data)
        except ValueError:
            self.sendAPI(1,400,'Send data in JSON')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def connectionMade(self):
        self.sendAPI(0,200,'Server ready')
        print 'connected'

    def connectionLost(self, reason):
        print 'disconnected'

