#!/usr/bin/python

from datetime import datetime
import time
import schedule
from model import User

def getTime():
    ts = datetime.now()
    return ts

userList={}

def searchUser(hashedUser):
    try:
        username=userList[hashedUser].name
        print (username);
    except (ValueError,KeyError):
        print ('not found')

def addUser(hashedUser,user):
    userList[hashedUser]=user

def removeUser(hashedUser):
    del userList[hashedUser]

def clearOldestEntries():
    for i,v in enumerate(userList):
        usert=userList[v]
        if(usert.timestamp < getTime()):
            removeUser(v)
        else:
            print ('kaas')

def inspectList():
    userList.keys()

def job():
    userList.clear() 

schedule.every(1).seconds.do(job)

arie=User('arie')
addUser("mde43a341sdaaw",arie)

while 1:
 schedule.run_pending()
 searchUser("mde43a341sdaaw")
 time.sleep(1)
