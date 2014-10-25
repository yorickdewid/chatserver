#!/usr/bin/python

from twisted.internet.protocol import Protocol
from model import User, Device, Chat 
import json
import uuid
import string
import random
import hashlib

class Echo(Protocol):

    def __init__(self):
        self.authenticated = None
        self.user = None

    def sendAPI(self, error, code, message, data = None, transport = None):
        api = {}
        api['error'] = error
        api['code'] = code
        api['message'] = message

        if data:
            api['data'] = data

        if transport:
            transport.write(json.dumps([api]) + '\n')
        else:
            self.transport.write(json.dumps([api]) + '\n')
 
    def clientPing(self, data):
        self.sendAPI(0,206,'Pong')

    def clientLastOnline(self, data):
        try:
            rdata = {}

            contact = User(data['username'])
            if contact.exist():
                rdata['last_online'] = unicode(contact.lastonline.replace(microsecond=0))
                for user in self.factory.clients:
                    if user.name == contact.name:
                        rdata['last_online'] = 'now'

                self.sendAPI(0,226,'Last online returned',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientRegister(self, data):
        try:
            rdata = {}

            username = data['username']
            user = User(username)
            if user.exist():
                self.sendAPI(1,441,'Credentials already exist')
                return

            user.token = self.getNewToken()
            user.password = self.getNewPassword()
            user.save()

            rdata['password'] = user.password
            self.sendAPI(0,241,'User registered',rdata)

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientRegisterDevice(self, data):
        try:
            if self.authenticated:
                self.user.update()
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
                self.user.update()
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
                self.user.update
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
                self.user.update()
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
            self.user.update()
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
                self.factory.clients.remove(self.user)
                self.user.delete()
                self.authenticated = None
                self.user = None
                self.sendAPI(0,291,'User data deleted')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientHello(self, data):
        try:
            rdata = {}

            if self.authenticated:
                self.user.update()
                self.sendAPI(0,110,'User authenticated')
                return

            user = User(data['username'])
            if user.attemptToken(data['token']):
                user.remote = self.transport.getPeer().host
                user.transport = self.transport
                user.uuid = uuid.uuid1()
                self.authenticated = 1
                self.user = user
                self.factory.clients.append(user)
                self.sendAPI(0,110,'User authenticated')

                for chat in self.factory.chats:
                    if chat.contact.name == user.name:
                        rdata['username'] = chat.user.name
                        rdata['port'] = chat.port
                        rdata['session'] = chat.session
                        rdata['remote'] = chat.user.remote
                        self.sendAPI(0,191,'Confirm chat request',rdata)

                print '%s is authenticated' % user
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientQuit(self, data = None):
        if self.authenticated:
            self.user.update()
            for chat in self.factory.chats[:]:
                if chat.user == self.user:
                    self.factory.chats.remove(chat)

            self.authenticated = None
            self.factory.clients.remove(self.user)
            self.user = None

        self.sendAPI(0,151,'Signed off')

    def clientRequestChat(self, data):
        try:
            rdata = {}
            cdata = {}

            if self.authenticated:
                self.user.update()
                contact = User(data['username'])
                if contact.exist():
                    request = Chat(self.user, contact, data['port'], uuid.uuid1().time_low)
                    self.factory.chats.append(request)
                    cdata['session'] = request.session

                    for other in self.factory.clients:
                        if contact.name == other.name:
                            rdata['username'] = self.user.name
                            rdata['port'] = request.port
                            rdata['session'] = request.session
                            rdata['remote'] = self.user.remote
                            self.sendAPI(0,191,'Confirm chat request',rdata,other.transport)

                    if rdata:
                        self.sendAPI(0,193,'Chat request pushed',cdata)
                    else:
                        self.sendAPI(0,192,'Chat request queued',cdata)
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientAcceptChat(self, data):
        try:
            rdata = {}

            if self.authenticated:
                self.user.update()
                try:
                    request = Chat(data['username'], self.user, data['port'], data['session'])
                    transport = self.factory.chats[self.factory.chats.index(request)].user.transport
                    rdata['session'] = data['session']
                    self.factory.chats.remove(request)
                    self.sendAPI(0,322,'Chat request accepted')
                    self.sendAPI(0,322,'Chat request accepted',rdata,transport)
                except ValueError:
                    self.sendAPI(1,420,'No request available')

            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

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
            190 : self.clientRequestChat,
            320 : self.clientAcceptChat,
        }[c]

    def getNewToken(self, input=None):
        if not input:
            input = str(self.getNewPassword())
        return hashlib.sha1(input).hexdigest()

    def getNewPassword(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def showLists(self):
        print 'online: %s' % len(self.factory.clients)
        print 'requests: %s' % len(self.factory.chats)

    def dataReceived(self, data):
        try:
            line = data.rstrip()
            if not line:
                return

            request = json.loads(line)[0]
            cdata = None
            code = request['code']
            error = request['error'] #TODO not used at the moment
            message = request['message'] #TODO not used at the moment

            if 'data' in request:
                cdata = request['data']
            
            self.handle(code)(cdata)
            self.showLists()
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

