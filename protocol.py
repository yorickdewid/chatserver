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
            rdata = {}

            user = User(data['username'])
            if user.exist():
                rdata['last_online'] = unicode(user.lastonline.replace(microsecond=0))
                self.sendAPI(0,226,'Last online returned',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def clientRegister(self, data):
        try:
            password = data['password']
            token = data['token']

            if len(password) != 8:
                self.sendAPI(1,405,'Password invalid')
                return

            if len(token) != 40:
                self.sendAPI(1,406,'Token invalid')
                return

            user = User(data['username'])
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
            user = User(data['username'])
            if user.attemptToken(data['token']):
                device = Device(data['device'])
                if device.exist():
                    self.sendAPI(1,436,'Device already exist')
                    return

                device.user = user
                if 'phone_number' in data:
                    device.phone_number = data['phone_number']

                user.addDevice(device)
                self.sendAPI(0,236,'Device registered')
            else:
                self.sendAPI(1,405,'Credentials invalid')

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

            user = User(data['username'])
            if user.attemptToken(data['token']):
                if 'contacts' in data:
                    for contact in data['contacts']:
                        contactuser = User(contact['contact'])
                        if contactuser.exist():
                            user.addContact(contactuser)

                for contact in user.getContactList():
                    rcontacts.append({'contact':contact.name})

                if len(rcontacts):
                    rdata['contacts'] = rcontacts

                self.sendAPI(0,211,'Contact list send',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDeleteContact(self, data):
        try:
            user = User(data['username'])
            if user.attemptToken(data['token']):
                for contact in data['contacts']:
                    contactuser = User(contact['contact'])
                    if contactuser.exist():
                        user.deleteContact(contactuser)

                self.sendAPI(0,276,'Contacts deleted')
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDeleteDevice(self, data):
        try:
            user = User(data['username'])
            if user.attemptToken(data['token']):
                device = Device(data['device'])
                if device.exist():
                    user.deleteDevice(device)

                self.sendAPI(0,266,'Device deleted')
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientGetDeviceList(self, data):
        try:
            rdata = {}
            rdevices = []

            user = User(data['username'])
            if user.attemptToken(data['token']):
                for device in user.getDeviceList():
                    rdevices.append({'device':device.device_id,'phone_number':device.phone_number})

                if len(rdevices):
                    rdata['devices'] = rdevices
                self.sendAPI(0,221,'Device list send',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDelete(self, data):
        try:
            user = User(data['username'])
            if user.attemptToken(data['token']):
                user.delete()
                self.sendAPI(0,291,'User data deleted')
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def handle(self, x):
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
        }[x]

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

        except ValueError:
            self.sendAPI(1,400,'Send data in JSON')
        except KeyError:
            self.sendAPI(1,401,'Not in reference format')

    def connectionMade(self):
        self.sendAPI(0,200,'Server ready')
        print 'connected'

    def connectionLost(self, reason):
        print 'disconnected'

