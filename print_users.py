#For Testing only

from database_setup import Student

students = session.query(Student).all()


for student in students:
    print student.name + " " + student.email
