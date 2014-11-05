#!/usr/bin/python

from twisted.internet.protocol import Protocol
from model import User, Device, Message
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

            username = data['username']
            if not username:
                self.sendAPI(1,447,'Value empty')
                return

            if not isinstance(username, basestring):
                self.sendAPI(1,448,'Value is wrong data type')
                return

            contact = User(username)
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
            if not username:
                self.sendAPI(1,447,'Value empty')
                return

            if not isinstance(username, basestring):
                self.sendAPI(1,448,'Value is wrong data type')
                return

            if len(username) > 50:
                self.sendAPI(1,449,'Value exceeds maximum input length')
                return

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
                device_id = data['device']
                if not device_id:
                    self.sendAPI(1,447,'Value empty')
                    return

                if len(device_id) > 120:
                    self.sendAPI(1,449,'Value exceeds maximum input length')
                    return

                device = Device(device_id)
                phone_number = data['phone_number']
                if not isinstance(phone_number, int):
                    self.sendAPI(1,448,'Value is wrong data type')
                    return

                if phone_number > 2147483646:
                    self.sendAPI(1,449,'Value exceeds maximum input length')
                    return

                if phone_number < 0:
                    self.sendAPI(1,447,'Value empty')
                    return

                if device.exist():
                    self.sendAPI(1,436,'Device already exist')
                    return

                device.user = self.user
                if 'phone_number' in data:
                    device.phone_number = phone_number

                self.user.addDevice(device)
                self.sendAPI(0,236,'Device registered')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientGetToken(self, data):
        try:
            rdata = {}

            username = data['username']
            if not username:
                self.sendAPI(1,447,'Value empty')
                return

            if not isinstance(username, basestring):
                self.sendAPI(1,448,'Value is wrong data type')
                return

            user = User(username)
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
                        ccontact = contact['contact']
                        if not ccontact:
                            self.sendAPI(1,447,'Value empty')
                            return

                        if not isinstance(ccontact, basestring):
                            self.sendAPI(1,448,'Value is wrong data type')
                            return

                        contactuser = User(ccontact)
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
                    ccontact = contact['contact']
                    if not ccontact:
                        self.sendAPI(1,447,'Value empty')
                        return

                    if not isinstance(ccontact, basestring):
                        self.sendAPI(1,448,'Value is wrong data type')
                        return

                    contactuser = User(ccontact)
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
                device_id = data['device']
                if not device_id:
                    self.sendAPI(1,447,'Value empty')
                    return

                if not isinstance(device_id, basestring):
                    self.sendAPI(1,448,'Value is wrong data type')
                    return

                device = Device(device_id)
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

            username = data['username']
            if not username:
                self.sendAPI(1,447,'Value empty')
                return

            if not isinstance(username, basestring):
                self.sendAPI(1,448,'Value is wrong data type')
                return

            user = User(username)
            if user.attemptToken(data['token']):
                user.remote = self.transport.getPeer().host
                user.transport = self.transport
                user.uuid = uuid.uuid1()
                self.authenticated = 1
                self.user = user
                self.factory.clients.append(user)
                self.sendAPI(0,110,'User authenticated')

                for message in self.factory.messages:
                    if message.contact.name == user.name:
                        rdata['username'] = message.user.name
                        rdata['session'] = message.session
                        rdata['message'] = message.message
                        rdata['cipher'] = message.cipher
                        rdata['timestamp'] = message.timestamp
                        self.sendAPI(0,191,'Message received',rdata)
            else:
                self.sendAPI(1,405,'Credentials invalid')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientQuit(self, data = None):
        if self.authenticated:
            self.user.update()
            for message in self.factory.messages[:]:
                if message.user == self.user:
                    self.factory.messages.remove(message)

            self.authenticated = None
            self.factory.clients.remove(self.user)
            self.user = None

        self.sendAPI(0,151,'Signed off')

    def clientReadMessage(self, data):
        try:
            rdata = {}

            if self.authenticated:
                self.user.update()
                try:
                    session = data['session']
                    if not isinstance(session, int):
                        self.sendAPI(1,448,'Value is wrong data type')
                        return

                    if session < 0:
                        self.sendAPI(1,447,'Value empty')
                        return

                    rmessage = Message(session)
                    transport = self.factory.messages[self.factory.messages.index(rmessage)].user.transport
                    rdata['session'] = session
                    self.factory.messages.remove(rmessage)
                    self.sendAPI(0,322,'Notification send')
                    self.sendAPI(0,324,'Message read',rdata,transport)
                except ValueError:
                    self.sendAPI(1,420,'No message available')

            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientMessage(self, data):
        try:
            rdata = {}
            cdata = {}

            if self.authenticated:
                self.user.update()
                cipher = data['cipher']
                if not cipher:
                    self.sendAPI(1,447,'Value empty')
                    return

                if not isinstance(cipher, basestring):
                    self.sendAPI(1,448,'Value is wrong data type')
                    return

                if cipher not in ['AES', 'PLAIN']:
                    self.sendAPI(1,417,'Cipher not supported')
                    return

                message = data['message']
                if not message:
                    self.sendAPI(1,447,'Value empty')
                    return

                if not isinstance(message, basestring):
                    self.sendAPI(1,448,'Value is wrong data type')
                    return

                timestamp = data['timestamp']
                if not timestamp:
                    self.sendAPI(1,447,'Value empty')
                    return

                if not isinstance(timestamp, basestring):
                    self.sendAPI(1,448,'Value is wrong data type')
                    return

                contact = data['username']
                if not contact:
                    self.sendAPI(1,447,'Value empty')
                    return

                if not isinstance(contact, basestring):
                   self.sendAPI(1,448,'Value is wrong data type')
                   return

                contactuser = User(contact)
                if contactuser.exist():
                    rmessage = Message(uuid.uuid1().time_low)
                    rmessage.user = self.user
                    rmessage.contact = contactuser
                    rmessage.message = message
                    rmessage.cipher = cipher
                    rmessage.timestamp = timestamp

                    self.factory.messages.append(rmessage)
                    cdata['session'] = rmessage.session
                    for other in self.factory.clients:
                        if contactuser.name == other.name:
                            rdata['username'] = self.user.name
                            rdata['session'] = rmessage.session
                            rdata['message'] = rmessage.message
                            rdata['cipher'] = rmessage.cipher
                            rdata['timestamp'] = rmessage.timestamp
                            self.sendAPI(0,191,'Message received',rdata,other.transport)

                    if rdata:
                        self.sendAPI(0,193,'Message pushed',cdata)
                    else:
                        self.sendAPI(0,192,'Message queued',cdata)
                else:
                   self.sendAPI(1,405,'Credentials invalid')
            else:
                self.sendAPI(1,410,'User unauthorized')

        except (KeyError, TypeError):
            self.sendAPI(1,401,'Not in reference format')

    def clientDefault(self, data):
        self.sendAPI(1,404,'Command does not exist')

    def handle(self, c):
        map = {
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
            320 : self.clientReadMessage,
            350 : self.clientMessage,
        }

        if c in map:
            return map[c]
        else:
            return self.clientDefault

    def getNewToken(self, input=None):
        if not input:
            input = str(self.getNewPassword())
        return hashlib.sha1(input).hexdigest()

    def getNewPassword(self, size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def showLists(self):
        print '--- status ---'
        print 'connections: %s ' % self.factory.connections
        print 'online: %s' % len(self.factory.clients)
        for user in self.factory.clients:
            print user
        print 'messages: %s' % len(self.factory.messages)
        for message in self.factory.messages:
            print message

    def dataReceived(self, data):
        try:
            line = data.rstrip()
            if not line:
                return

            request = json.loads(line)[0]
            cdata = None
            code = request['code']
            error = request['error']
            message = request['message']

            if 'data' in request:
                cdata = request['data']
            
            self.handle(code)(cdata)
        except ValueError:
            self.sendAPI(1,400,'Send data in JSON')
        except (KeyError, IndexError):
            self.sendAPI(1,401,'Not in reference format')

    def connectionMade(self):
        self.factory.connections += 1
        self.sendAPI(0,200,'Server ready')
        self.showLists()
        print 'connect from %s' % self.transport.getPeer()

    def connectionLost(self, reason):
        self.factory.connections -= 1
        self.clientQuit()
        print 'disconnect from %s' % self.transport.getPeer()

