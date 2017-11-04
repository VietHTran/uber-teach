from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Student, Course, University, Base 
 
engine = create_engine('sqlite:///uber-teach-db.db')
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()
session.commit()

university1 = University(name = "Pennsylvania State University")
session.add(university1)
session.commit()

university2 = University(name = "University of Pennsylvania")
session.add(university1)
session.commit()

course1 = Course(name="CMPSC360", university_id="1")
session.add(course1)
session.commit()

course2 = Course(name="CMPEN271", university_id="1")
session.add(course2)
session.commit()

course3 = Course(name="MATH250", university_id="2")
session.add(course3)
session.commit()

course4 = Course(name="HIST20", university_id="2")
session.add(course4)
session.commit()

admin = Student(username="admin", name="admin", password="admin", email="vht1@psu.edu", university_id="1", is_admin=True)
session.add(admin)
session.commit()

student1 = Student(username="student1", name="Johnny Sins", password="plumber", email="jxs1@psu.edu", university_id="2", is_admin=False)
session.add(student1)
session.commit()

student2 = Student(username="student2", name="Riley Reid", password="putbackin", email="rxr1@psu.edu", university_id="1", is_admin=False)
session.add(student2)
session.commit()

print "Finish adding stuff"
