#!/usr/bin/python

import MySQLdb

# Open database connection
db = MySQLdb.connect("localhost","python","ABC@123","chatapp" )

# prepare a cursor object using cursor() method
cursor = db.cursor()

# execute SQL query using execute() method.
cursor.execute("SELECT * from user")

# Fetch a single row using fetchone() method.
data = cursor.fetchall()

for row in data:
    print "User %s was last online at %s" % (row[1], row[3])

# disconnect from server
db.close()
