#!/usr/bin/python

import MySQLdb

class User:
    'User class'

    def __init__(self, name):
        self.name = name.lower()
        self.token = None
        self.password = None
        self.lastonline = None
        self.remote = None
        self.transport = None
        self.uuid = None
        self.db = MySQLdb.connect('localhost','python','ABC@123','chatapp')
        self.cursor = self.db.cursor()

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __str__(self):
        return '%s[%s]' % (self.name, self.uuid)

    def getUser(self):
        self.cursor.execute('SELECT * FROM user WHERE username=%s', self.name)
        row = self.cursor.fetchone()
        if not row:
            return;

        self.token = row[1]
        self.password = row[3]
        self.lastonline = row[2]

    def exist(self):
        self.getUser()

        if self.token and self.lastonline:
           return 1

    def attemptToken(self, token):
        if self.exist():
            if self.token == token:
                self.update()
                return 1

    def attemptPassword(self, password):
        if self.exist():
            if self.password == password:
                self.update()
                return 1

    def update(self):
        self.cursor.execute('UPDATE user SET last_online=NOW() WHERE username=%s', self.name)
        self.db.commit()

    def getContactList(self):
        contactlist = []
        self.cursor.execute('SELECT * FROM contactlist WHERE username=%s', self.name)
        rows = self.cursor.fetchall()
        for row in rows:
            user = User(row[1])
            user.getUser()
            contactlist.append(user)
        return contactlist

    def addContact(self, user):
        try:
            self.cursor.execute('INSERT INTO contactlist VALUES (%s, %s)', (self.name, user.name))
            self.db.commit()
        except:
            self.db.rollback()

    def deleteContact(self, user):
        self.cursor.execute('DELETE FROM contactlist WHERE username=%s AND contactname=%s', (self.name, user.name))
        self.db.commit()

    def getDeviceList(self):
        devicelist = []
        self.cursor.execute('SELECT * FROM device WHERE user=%s', self.name)
        rows = self.cursor.fetchall()
        for row in rows:
            device = Device(row[0])
            device.getDevice()
            devicelist.append(device)
        return devicelist

    def addDevice(self, device):
        try:
            self.cursor.execute('INSERT INTO device VALUES (%s, %s, %s)', (device.device_id, device.phone_number, self.name))
            self.db.commit()
        except:
            self.db.rollback()

    def deleteDevice(self, device):
        self.cursor.execute('DELETE FROM device WHERE user=%s AND device_id=%s', (self.name, device.device_id))
        self.db.commit()

    def save(self):
        try:
            self.cursor.execute('INSERT INTO user VALUES (%s, %s, NOW(), %s)',
                (self.name, self.token, self.password))
            self.db.commit()
        except:
            self.db.rollback()

    def delete(self):
        self.cursor.execute('DELETE FROM user WHERE username=%s', (self.name))
        self.db.commit()

    def __del__(self):
        self.db.close()

class Device:
    'Device class'

    def __init__(self, id):
        self.device_id = id.lower()
        self.phone_number = 0
        self.user = []
        self.db = MySQLdb.connect('localhost','python','ABC@123','chatapp')
        self.cursor = self.db.cursor()

    def __eq__(self, other):
        return self.device_id == other.device_id

    def getDevice(self):
        self.cursor.execute('SELECT * FROM device WHERE device_id=%s', self.device_id)
        row = self.cursor.fetchone()
        if not row:
            return;

        self.device_id = row[0]
        self.phone_number = row[1]
        user = User(row[2])
        user.getUser()
        self.user = user

    def exist(self):
        self.getDevice()

        if self.user:
           return 1

    def save(self):
        try:
            self.cursor.execute('INSERT INTO device VALUES (%s, %s, %s)',
                (self.device_id, self.phone_number, self.user.name))
            self.db.commit()
        except:
            self.db.rollback()

    def delete(self):
        self.cursor.execute('DELETE FROM device WHERE device_id=%s', (self.device_id))
        self.db.commit()

    def __del__(self):
        self.db.close()

class Message:
    'Message class'

    def __init__(self, session):
        self.user = None
        self.contact = None
        self.cipher = None
        self.session = session
        self.message = None
        self.timestamp = None

    def __eq__(self, other):
        return self.session == other.session

    def __str__(self):
        return '%s<-[%s]->%s' % (self.user.name, self.session, self.contact.name)
