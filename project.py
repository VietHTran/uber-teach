from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError 
import httplib2
import json
from flask import make_response
import requests

#Connect to Database and create database session
engine = create_engine('sqlite:///uber-teach-db.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def generateResponse(message, code):
    response = make_response(json.dumps(message), code)
    response.headers['Content-Type'] = 'application/json'
    return response

def generateAlertOutput(message):
    output = ''
    output += '<script>function alertMessage() { alert("' 
    output += message
    output += '");}</script><body onLoad="alertMessage()"></body>'
    return output

def generateLoginWelcome():
    if 'username' not in login_session or 'picture' not in login_session:
        return None
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

def getHttpResult(url):
    h = httplib2.Http()
    return h.request(url, 'GET')[1]

def createUser(login_session):
    if ('username' in login_session):
        newUser = User(name = login_session['username'],
                email = login_session['email'],
                picture = login_session['picture'])
        session.add(newUser)
        session.commit()
        user = session.query(User).filter_by(email = login_session['email']).one()
        return user.id
    return None

def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id = user_id).one()
        return user
    except:
        return None

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)



