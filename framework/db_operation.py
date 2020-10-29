import pymongo
import json
from bson.json_util import dumps
from bson.objectid import ObjectId
from json_template import a
import datetime

connect = pymongo.MongoClient("mongodb://localhost:27017/")
db = connect['math_point']
student = db['students']
course = db['course']


def verify_email_reg(email):
    response = student.find_one({"email": email})
    if response:
        return {"flag":1,"data":{'ids': str(response["_id"]),'email':str(email)}}
    else:
        a["email"]=str(email)
        student.insert_one(a)
        student.update({"email": email},{"$set":{"time_date": datetime.datetime.utcnow()}})
        response = student.find_one({"email": email})
        return {"flag":0,"data":{'ids': str(response["_id"]),'email':str(email)}}


def verify_email_log(users_email):
    response = student.find_one({"email": users_email})
    if response:
         return {'ids': str(response["_id"]),'email':response["email"],'gender':response["gender"]}
    else:
         return 0


def saving_form_info(data,id):
    try:
        if student.find_one({"_id": ObjectId(id)})["student_name"] == "":
            student.update({"_id": ObjectId(id)},{"$set":{"student_name":data["std_name"],"course":data["select1"],"dob":data["date"],"student_mob":data["std_mob"],"parent_mob":data["parant_mob"],"gender":data['options']}})
            return 1
        else:
            return "already user in db"
    except:
        return 0

def index_page():
    return dumps(course.find({},{"_id":False}))

def my_courses(ids):
    student_db = student.find_one({"_id": ObjectId(ids)},{"_id":False})
    if student_db == None:
        return 0
    else:
        return dumps(course.find_one({"tital":student_db["course"]},{"links":True,"_id":False}))


def courses_details_data(data):
    course_db = course.find_one({"tital":data},{"links":True,"_id":False,"price":True,})
    if course_db == None:
        return 0
    else:
        return course_db