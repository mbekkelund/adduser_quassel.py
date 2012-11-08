#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#  
#  This little python-script creates a little login-form
#  where users can enter their ldap-username and password,
#  have it verified and if its validated it will insert 
#  (or update an existing) row in quassels sqlite-databse.
#
#  Requirements are: python, python-bottle and python-ldap.
#  The script needs to run on the same server as quassel-core.
#  
#  Copyright (C) 2012 Morten Bekkelund
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#  
#  See: http://www.gnu.org/copyleft/gpl.html


import hashlib
import sqlite3
import sys
import ldap
from bottle import route,run,template,request

# settings
listen="localhost" # what address to listen to
port=8080 # the port on which this app will run
quassel_base="/var/lib/quassel/quassel-storage.sqlite" # location of the quassel sqlite-database
ldap_server='ldap://ldap.example.com' # your ldap-server
ldap_base="ou=user,ou=internal,dc=example,dc=com" # your ldap base dn


@route('/login', method='GET') 
def login_form():
    return '''Log in with your LDAP username and password to register a Quassel-user<p>
             <form method="POST" action="/login">
                User <input name="name"     type="text" />
                Password <input name="password" type="password" />
                <input type="submit" />
              </form>'''

@route('/login', method='POST')
def login_submit():
    ''' reading form-values, checking if its a valid ldap-user, inserts or updates the user in the quassel sqlite-base '''
    name = request.POST.get('name','').strip()
    form_password = request.POST.get('password','').strip()
    password = hashlib.sha1(form_password).hexdigest()
    if check_login(name, form_password):
        try:
            conn = sqlite3.connect(quassel_base)
        except:
            return "Cannot connect to the sqlite-base."
            sys.exit(1)
        c = conn.cursor()
        try: 
            c.execute("insert into quasseluser values (NULL,'{0}','{1}')".format(name,password));
            conn.commit()
        except:
            c.execute("update quasseluser set password='{1}' where userid = \
                (select userid from quasseluser where username='{0}')".format(name,password));
            conn.commit()
            return "Existing user successfully updated! <a href='http://{0}:{1}/login'>Back</a>".format(listen,port)
        conn.close()
        return "<p>New user successfully added. You can now connect to Quassel.<a href='http://{0}:{1}/login'>Back</a></p>".format(listen,port)
    else:
        return "<p>LDAP-login failed. <a href='http://{0}:{1}/login'>Back</a></p>".format(listen,port)

def check_login(name, password):
    ''' checking if the user can bind to ldap '''
    l = ldap.initialize(ldap_server)
    user = "uid=%s,%s"%(name,ldap_base)
    try: 
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(user,password)
        return True
    except Exception, error:
        print error

run(host=listen,port=port)
