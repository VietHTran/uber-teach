import flask
import datetime 
from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine, asc, and_ 
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

def getCourseInfoById(course_id):
    try:
        course = session.query(Course).filter_by(id = course_id).one()
        return course 
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

def getUniInfoById(university_id):
    try:
        university = session.query(University).filter_by(id = university_id).one()
        return university 
    except:
        return None

def getCoursesInfoByStudentId(student_id):
    try:
        courses = []
        enrollments = session.query(Enrollment).filter_by(student_id = student_id)
        for enrollment in enrollments:
            course = session.query(Course).filter_by(id = enrollment.course_id).one()
            courses.append(course)
        return courses 
    except Exception as ex:
        return None

def updateStudentInfo(username, name, newCourses):
    try:
        student = getStudentInfoByUsername(username)
        student.name = name
        session.commit()
        enrollments = session.query(Enrollment).filter_by(student_id = student.id)
            
        for enrollment in enrollments:
            course = session.query(Course).filter_by(id = enrollment.course_id).one()
            if not(course.name in newCourses):
                session.delete(enrollment)
                session.commit()
            else:
                newCourses.remove(course.name)
        for newCourse in newCourses:
            print newCourse
            course = session.query(Course).filter_by(name = newCourse).one()
            if session.query(Course).filter_by(name = newCourse).count() == 0:
                continue
            print course.name
            enrollment = Enrollment(
                    student_id = student.id, 
                    course_id = course.id,
                    credits = 0)
            session.add(enrollment)
            session.commit()
        return True 
    except:
        return False 

def getYourRequests(username):
    try:
        student = getStudentInfoByUsername(username)
#        requests = session.query(HelpRequest).filter_by(
#                student_id = student.id).order_by(HelpRequest.date)
        requests = session.query(HelpRequest).filter_by(
                student_id = student.id)
        return requests 
    except:
        print "err1"
        return None 
    
def getRequestsForUser(username):
    try:
        student = getStudentInfoByUsername(username)
        courses = getCoursesInfoByStudentId(student.id)
        courseIds = [course.id for course in courses]
#        requests = session.query(HelpRequest).filter_by(and_(HelpRequest.course_id.in_(courseIds),HelpRequest.status.like("OPEN")))
        
        requests = session.query(HelpRequest).filter(
                HelpRequest.course_id.in_(courseIds), 
                HelpRequest.status == "OPEN").all()
        return requests 
    except Exception as ex:
        print str(ex)
        return None 

def getRequestsInProgress(username):
    try:
        student = getStudentInfoByUsername(username)
        requests = session.query(HelpRequest).filter_by(
                helper_id = student.id,
                status = "PROGRESS")
        return requests 
    except:
        print "err3"
        return None 

def updateRequestStatus(requestId, status, username):
    try:
        request = session.query(HelpRequest).filter_by(id = requestId).one()
        request.status = status
        if status == 'PROGRESS':
            student = session.query(Student).filter_by(username = username).one()
            request.helper_id = student.id
        session.commit()
        return True
    except:
        return False

def deleteRequest(requestId):
    try:
        request = session.query(HelpRequest).filter_by(id = requestId).one()
        session.delete(request)
        session.commit()
        return True
    except:
        return False

def closeRequest(requestId):
    try:
        req = session.query(HelpRequest).filter_by(id = requestId).one()
        enrollment = session.query(Enrollment).filter_by(student_id = req.helper_id, id = req.course_id).one()
        enrollment.credits += 1
        session.commit()
        if updateRequestStatus(requestId, "CLOSED", ""):
            return True
        return False 
    except Exception as ex:
        print "Close Request Error: "
        print str(ex)
        return False

def getEnrollmentByUsername(username):
    try:
        student = session.query(Student).filter_by(username = username).one()
        enrollments = session.query(Enrollment).filter_by(student_id = student.id)
        courses = []
        for enrollment in enrollments:
            course = session.query(Course).filter_by(id = enrollment.course_id).one()
            holder = {
                    'course': course,
                    'credits': enrollment.credits
                    }
            courses.append(holder)
        return courses
    except Exception as ex:
        return None 
# Login page
@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        students = session.query(Student).all()
        if 'username' in login_session:
            return flask.redirect(flask.url_for('dashboard'))
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE = state)
    else:
        usernameInput = request.form['username']
        passwordInput = request.form['password']
        if  usernameInput == '' or passwordInput == '':
            return generateResponse('Empty input field', 401) 
        student = getStudentInfoByUsername(usernameInput)
        if student == None or student.password != passwordInput:
            return generateResponse('Incorrect username or password', 401)
        login_session['username'] = usernameInput
        return flask.redirect(flask.url_for('dashboard'))
        # return flask.redirect(flask.url_for('profile', username = student.username))

#Register page
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
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
        student = getStudentInfoByUsername(usernameInp)
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
                university_id = university.id,
                is_admin = False) 
        session.add(newStudent)
        session.commit()
        login_session['username'] = usernameInp
        return flask.redirect(flask.url_for('profile', username = usernameInp))

@app.route('/logout')
def logout():
    if 'username' in login_session:
        del login_session['username']
        return flask.redirect(flask.url_for('login'))

@app.route('/profile/<username>/')
def profile(username):
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    editBtnVisibility = 'collapse'
    if username == login_session['username']:
        editBtnVisibility = 'visible'
    student = getStudentInfoByUsername(username)
    university = getUniInfoById(student.university_id)
    data = getEnrollmentByUsername(username)
    if data == None:
        return generateResponse("Error getting courses and enrollments", 401)
    return render_template('profile.html',
            username = username,
            name = student.name,
            email = student.email,
            university = university.name,
            data = data,
            editBtnVisibility = editBtnVisibility)

@app.route('/editprofile', methods = ['GET', 'POST'])
def editProfile():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    username = login_session['username']
    if request.method == 'GET':
        username = login_session['username']
        student = getStudentInfoByUsername(username)
        university = getUniInfoById(student.university_id)
        courses = getCoursesInfoByStudentId(student.id) 
        return render_template('editprofile.html',
                username = username,
                name = student.name,
                email = student.email,
                university = university.name,
                courses = courses)
    elif request.method == 'POST':
        nameInp = request.form['name']
        courses = request.form.getlist('course')
        if nameInp == '':
            student = getStudentInfoByUsername(username)
            nameInp = student.name 
        if updateStudentInfo(username, nameInp, courses):
            print "Update profile successfully"
        else:
            print "Update profile failed"
        return flask.redirect(flask.url_for('profile', username = login_session['username']))

@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    username = login_session['username']
    posted = []
    postedRequests = getYourRequests(username) 
    for pr in postedRequests:
        holder = {
                'request': pr,
                'student': getStudentInfoById(pr.student_id),
                'course': getCourseInfoById(pr.course_id)
                }
        posted.append(holder)

    opn = []
    openRequests = getRequestsForUser(username) 
    for orq in openRequests:
        print orq.subject + "\t" + orq.description
        student = getStudentInfoById(orq.student_id)
        if student.username == username:
            continue
        holder = {
                'request': orq,
                'student': getStudentInfoById(orq.student_id),
                'course': getCourseInfoById(orq.course_id)
                }
        opn.append(holder)
    working = []
    workingRequests = getRequestsInProgress(username) 
    for wr in workingRequests:
        holder = {
                'request': wr,
                'student': getStudentInfoById(wr.student_id),
                'course': getCourseInfoById(wr.course_id)
                }
        working.append(holder)
    return render_template('dashboard.html',
            posted= posted,
            opn= opn,
            working= working)

@app.route('/dashboard/accept', methods = ['POST'])
def acceptRequest():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    requestId = request.form['request_id']
    if updateRequestStatus(requestId, "PROGRESS", login_session['username']):
        print "Update request successful"
    else:
        print "Update request failed"
    return flask.redirect(flask.url_for('dashboard'))

@app.route('/dashboard/cancel', methods = ['POST'])
def cancelTutor():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    requestId = request.form['request_id']
    if updateRequestStatus(requestId, "OPEN", ""):
        print "Update request successful"
    else:
        print "Update request failed"
    return flask.redirect(flask.url_for('dashboard'))

@app.route('/dashboard/complete', methods = ['POST'])
def completeTutoring():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    requestId = request.form['request_id']
    if closeRequest(requestId):
        print "Update request successful"
    else:
        print "Update request failed"
    return flask.redirect(flask.url_for('dashboard'))

@app.route('/dashboard/delete', methods = ['POST'])
def deleteRequestRoute():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    requestId = request.form['request_id']
    if deleteRequest(requestId):
        print "Delete request successful"
    else:
        print "Delete request failed"
    return flask.redirect(flask.url_for('dashboard'))

@app.route('/admin/add_university', methods = ['GET', 'POST'])
def addUniversity():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    elif login_session['username'] != 'admin':
        return flask.redirect(flask.url_for('dashboard'))
    if request.method == 'GET':
        return render_template('adminuniversity.html')
    elif request.method == 'POST':
        newUniversity = University(name = request.form['name'])
        session.add(newUniversity)
        session.commit()
        return flask.redirect(flask.url_for('dashboard'))

@app.route('/admin/add_course', methods = ['GET', 'POST'])
def addCourse():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    elif login_session['username'] != 'admin':
        return flask.redirect(flask.url_for('dashboard'))
    if request.method == 'GET':
        universities = session.query(University).all()
        return render_template('admincourse.html', universities = universities)
    elif request.method == 'POST':
        newCourse = Course(
                name = request.form['name'], 
                university_id = request.form['university_id'])
        session.add(newCourse)
        session.commit()
        return flask.redirect(flask.url_for('dashboard'))

@app.route('/requesthelp', methods = ['GET', 'POST'])
def requestHelp():
    if not ('username' in login_session):
        return flask.redirect(flask.url_for('login'))
    username = login_session['username']
    student = getStudentInfoByUsername(username)
    if request.method == 'GET':
        courses = getCoursesInfoByStudentId(student.id)
        return render_template('requesthelp.html', courses = courses)
    elif request.method == 'POST':
        subjectInp = request.form['subject']
        descriptionInp = request.form['description']
        locationInp = request.form['location']
        courseInp = request.form['course']
        if subjectInp == '' or locationInp == '':
            return generateResponse('Please enter the required field', 401)
        helpRequest = HelpRequest(
                student_id = student.id,
                subject = subjectInp,
                description = descriptionInp,
                location = locationInp,
                course_id = courseInp,
                status = "OPEN")
        session.add(helpRequest)
        session.commit()
        return flask.redirect(flask.url_for('dashboard'))
        

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
