from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Float, DateTime, Boolean 
from sqlalchemy import create_engine
 
Base = declarative_base()

class University(Base):
    __tablename__ = 'university'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class Course(Base):
    __tablename__ = 'course'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    university_id = Column(Integer, ForeignKey('university.id'))

    @property
    def serialize(self):
       return {
           'name'         : self.name,
           'id'           : self.id,
           'university_id': self.university_id,
       }

class Student(Base):
    __tablename__ = 'student'
   
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False, unique=True)
    name = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    university_id = Column(Integer, ForeignKey('university.id'))
    is_admin = Column(Boolean, nullable=False)

    @property
    def serialize(self):
       return {
           'id'           : self.id,
           'username'     : self.username,
           'name'         : self.name,
           'password'     : self.password,
           'email'        : self.email,
           'university_id': self.university_id,
           'is_admin'     : self.is_admin,
       }

class Enrollment(Base):
    __tablename__ = 'enrollment'
   
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'))
    course_id = Column(Integer, ForeignKey('course.id'))
    credits = Column(Integer)

    @property
    def serialize(self):
       return {
           'id'           : self.id,
           'student_id'   : self.student_id,
           'course_id'    : self.university_id,
           'credits'      : self.credits,
       }

class Transaction(Base):
    __tablename__ = 'transaction'
   
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey('student.id'))
    to_user_id = Column(Integer,  ForeignKey('student.id'))
    amount = Column(Float, nullable=False)

    @property
    def serialize(self):
       return {
           'id'           : self.id,
           'student_id'   : self.student_id,
           'course_id'    : self.university_id,
           'amount'      : self.amount,
       }

class HelpRequest(Base):
    __tablename__ = 'help_request'
   
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'))
    subject = Column(String, nullable=False)
    description = Column(String)
    location = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    status = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    helper_id = Column(Integer, ForeignKey('student.id'))
    amount = Column(Float, nullable=False)

    @property
    def serialize(self):
       return {
           'id'           : self.id,
           'student_id'   : self.student_id,
           'subject'      : self.subject,
           'description'  : self.description,
           'location'     : self.location,
           'course_id'    : self.university_id,
           'status'       : self.status,
           'date'         : self.date,
           'amount'       : self.amount,
       }

engine = create_engine('sqlite:///uber-teach-db.db')
Base.metadata.create_all(engine)
