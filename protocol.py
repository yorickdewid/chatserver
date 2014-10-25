#!/usr/bin/python

from twisted.internet.protocol import Protocol
from model import User, Device 
import json
import uuid

class Echo(Protocol):

    def __init__(self):
        self.authenticated = None
        self.user = None

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
            rdata = {}

            contact = User(data['username'])
            if contact.exist():
                rdata['last_online'] = unicode(contact.lastonline.replace(microsecond=0))
                self.sendAPI(0,226,'Last online returned',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
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
            if user.exist():
                self.sendAPI(1,441,'Credentials already exist')
                return

            user.token = token
            user.password = password
            user.save()

            self.sendAPI(0,241,'User registered')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientRegisterDevice(self, data):
        try:
            if self.authenticated:
                device = Device(data['device'])
                if device.exist():
                    self.sendAPI(1,436,'Device already exist')
                    return

                device.user = self.user
                if 'phone_number' in data:
                    device.phone_number = data['phone_number']

                self.user.addDevice(device)
                self.sendAPI(0,236,'Device registered')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientGetToken(self, data):
        try:
            rdata = {}

            user = User(data['username'])
            if user.attemptPassword(data['password']):
                rdata['token'] = user.token
                self.sendAPI(0,246,'Token returned',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientGetContactList(self, data):
        try:
            rdata = {}
            rcontacts = []

            if self.authenticated:
                if data:
                    for contact in data['contacts']:
                        contactuser = User(contact['contact'])
                        if contactuser.exist():
                            self.user.addContact(contactuser)

                for contact in self.user.getContactList():
                    rcontacts.append({'contact':contact.name})

                if len(rcontacts):
                    rdata['contacts'] = rcontacts

                self.sendAPI(0,211,'Contact list send',rdata)
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDeleteContact(self, data):
        try:
            if self.authenticated:
                for contact in data['contacts']:
                    contactuser = User(contact['contact'])
                    if contactuser.exist():
                        self.user.deleteContact(contactuser)

                self.sendAPI(0,276,'Contacts deleted')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDeleteDevice(self, data):
        try:
            if self.authenticated:
                device = Device(data['device'])
                if device.exist():
                    self.user.deleteDevice(device)

                self.sendAPI(0,266,'Device deleted')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientGetDeviceList(self, data):
        rdata = {}
        rdevices = []

        if self.authenticated:
            for device in self.user.getDeviceList():
                rdevices.append({'device':device.device_id,'phone_number':device.phone_number})

            if len(rdevices):
                rdata['devices'] = rdevices
            self.sendAPI(0,221,'Device list send',rdata)
        else:
            self.sendAPI(1,410,'User unauthorized')

    def clientDelete(self, data):
        try:
            if self.authenticated:
                self.user.delete()
                self.authenticated = None
                self.sendAPI(0,291,'User data deleted')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientHello(self, data):
        try:
            if self.authenticated:
                self.sendAPI(0,110,'User authenticated')
                return

            user = User(data['username'])
            if user.attemptToken(data['token']):
                user.remote = self.transport.getPeer().host
                user.transfer = self
                user.uuid = uuid.uuid1()
                self.authenticated = 1
                self.user = user
                self.factory.clients.append(user)
                self.sendAPI(0,110,'User authenticated')
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientQuit(self, data = None):
        if self.authenticated:
            self.authenticated = None
            self.factory.clients.remove(self.user)
            self.user = None

        self.sendAPI(0,151,'Signed off')

    def handle(self, c):
        return {
            205 : self.clientPing,
            240 : self.clientRegister,
            245 : self.clientGetToken,
            225 : self.clientLastOnline,
            235 : self.clientRegisterDevice,
            210 : self.clientGetContactList,
            275 : self.clientDeleteContact,
            260 : self.clientDeleteDevice,
            220 : self.clientGetDeviceList,
            290 : self.clientDelete,
            100 : self.clientHello,
            150 : self.clientQuit,
        }[c]

    def dataReceived(self, data):
        try:        
            req = json.loads(data.rstrip())[0]
            data = None
            code = req['code']
            error = req['error'] #TODO not used at the moment
            message = req['message'] #TODO not used at the moment

            if 'data' in req:
                data = req['data']

            self.handle(code)(data)

            for c in self.factory.clients:
                print c.name, c.uuid

        except ValueError:
            self.sendAPI(1,400,'Send data in JSON')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def connectionMade(self):
        self.sendAPI(0,200,'Server ready')
        print 'connect from %s' % self.transport.getPeer()

    def connectionLost(self, reason):
        self.clientQuit()
        print 'disconnect from %s' % self.transport.getPeer()

