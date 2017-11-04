import flask
from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, University, Course, Student, Transaction, HelpRequest, Enrollment
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

def getHttpResult(url):
    h = httplib2.Http()
    return h.request(url, 'GET')[1]

def getStudentInfoById(student_id):
    try:
        student = session.query(Student).filter_by(id = student_id).one()
        return student 
    except:
        return None

def getStudentInfoByUsername(username):
    try:
        student = session.query(Student).filter_by(username = username).one()
        return student 
    except:
        return None

def getStudentInfoByEmail(email):
    try:
        student = session.query(Student).filter_by(email = email).one()
        return student 
    except:
        return None

def getUniInfoByName(name):
    try:
        university = session.query(University).filter_by(name = name).one()
        return university 
    except:
        return None

# Login page
@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        students = session.query(Student).all()
        for student in students:
            print student.name + " " + student.password
        if 'username' in login_session:
            flask.redirect(flask.url_for('dashboard'))
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE = state)
    else:
        usernameInput = request.form['username']
        passwordInput = request.form['password']
        if  usernameInput == '' or passwordInput == '':
            return generateResponse('Empty input field', 401) 
        student = getStudentInfoByUsername(usernameInput)
        print str(student)
        if student == None or student.password != passwordInput:
            return generateResponse('Incorrect username or password', 401)
        login_session['username'] = usernameInput
        flask.redirect(flask.url_for('dashboard'))

#Register page
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        usernameInp = request.form['username']
        nameInp = request.form['name']
        emailInp = request.form['email']
        passwordInp = request.form['password']
        confpasswordInp = request.form['confirm_password']
        universityInp = request.form['university']

        if  usernameInp == '' or passwordInp == '' or emailInp == '' or universityInp == '':
            return generateResponse('Empty input field', 401) 
        elif confpasswordInp != passwordInp:
            return generateResponse('Confirm password does not match', 401) 

        university = getUniInfoByName(universityInp)
        student = getStudentInfoByUsername(usernameInput)
        studentEmail = getStudentInfoByEmail(emailInp)

        if student != None:
            return generateResponse('Username already exists', 401)
        elif university == None:
            return generateResponse('University not found', 401)
        elif studentEmail != None:
            return generateResponse('Email already exists', 401)
        newStudent = Student(name=nameInp, 
                username = usernameInp,
                email = emailInp,
                password = passwordInp,
                university_id = university.id) 
        session.add(newStudent)
        session.commit()
        login_session['username'] = usernameInput
        flask.redirect(flask.url_for('profile/%s/' % usernameInp))

@app.route('/logout')
def logout():
    if 'username' in login_session:
        del login_session['username']
        flask.redirect(flask.url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)

