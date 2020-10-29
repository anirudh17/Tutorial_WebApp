import pymongo
from flask import Flask, session, render_template, url_for, send_file, jsonify, request, redirect, make_response, abort
from flask_socketio import SocketIO, emit
import json
import os
from bson.json_util import dumps
from datetime import date, datetime, timedelta
from flask_session import Session
import hashlib
import re

import db_operation

from flask_cors import CORS

from flask_restful import Api, Resource

from oauthlib.oauth2 import WebApplicationClient
import requests

# Configuration
GOOGLE_CLIENT_ID = "103094677665rdlsdo.apps.googleusercontent.com"# Create your own (This is wrong key)
GOOGLE_CLIENT_SECRET = "q0EWoaW9"# Create your own (This is wrong key)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Covid_secret6'

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_FILE_THRESHOLD'] = 800

socketio = SocketIO(app)
Session(app)
api = Api(app)
# CORS(app)

# -------------------------------------all Google setup------------------------------------------------

client = WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/register', methods=["GET"])
def reg():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["email"],
    )
    return redirect(request_uri)


@app.route('/register/callback', methods=["GET", "POST"])
def callback_reg():
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        # unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        # users_name = userinfo_response.json()["given_name"]
        # return json.dumps([unique_id,users_email,picture])
        data = db_operation.verify_email_reg(users_email)
        if data["flag"] != 1:
            data = data["data"]
            session[data["ids"]] = data['email']
            return redirect(url_for('register_get', ids=data['ids']))
        else:
            data = data["data"]
            session[str(data["ids"])] = data['email']
            return redirect(url_for('sign_up', dat="Please Sign In!"))
    else:
        return "Email Id not Verified, Please Verify it on Gmail", 400


@app.route('/login', methods=["GET"])
def login():
        # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["email"],
    )
    return redirect(request_uri)


@app.route('/login/callback', methods=["GET", "POST"])
def callback():
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        # unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        # users_name = userinfo_response.json()["given_name"]
        # return json.dumps([unique_id,users_email,picture])
        data = db_operation.verify_email_log(users_email)
        if data != 0:
            if data["gender"] != "":
                session[data["ids"]] = data['email']
                return redirect(url_for('home', ids=data['ids']))
            else:
                session[data["ids"]] = data['email']
                return redirect(url_for('register_get', ids=data["ids"]))
        else:
            return redirect(url_for('sign_in', dat="Not Register Yet.Please Sign Up!"))
    else:
        return "Email Id not Verified, Please Verify it on Gmail", 400


# ------------------------------------------====== End of Google ======------------------------------


@app.route('/sign_up', methods=["GET"])
def sign_up():
    return render_template('email_verification.html')


@app.route('/sign_in', methods=["GET"])
def sign_in():
    return render_template('login.html')


@app.route('/index/<ids>', methods=["GET"])
@app.route('/index')
def home(ids=None):
    if session.get(ids) == None:
        return render_template('index.html', ids=None)
    else:
        return render_template('index.html', ids=ids)


@app.route('/about', methods=["GET"])
def about():
    return render_template('login.html')


@app.route('/course/<ids>', methods=["GET"])
@app.route('/course', methods=["GET"])
def course(ids=None):
    if session.get(ids) == None:
        return render_template('cource.html', ids=None)
    else:
        return render_template('cource.html', ids=ids)


@app.route('/my_courses', methods=["GET"])
@app.route('/my_courses/<ids>', methods=["GET"])
def my_courses(ids=None):
    if session.get(ids) == None:
        return render_template('my_courses.html', ids=None)
    else:
        return render_template('my_courses.html', ids=ids)


@app.route('/course_details', methods=["GET"])
@app.route('/course_details/<ids>', methods=["GET"])
def course_details(ids=None):
    if session.get(ids) == None:
        return render_template('course_details.html', ids=None)
    else:
        return render_template('course_details.html', ids=ids)


@app.route('/register/<ids>', methods=["GET"])
def register_get(ids):
    return render_template('sign_up_form.html')


@app.route('/register/<ids>', methods=["POST"])
def register_post(ids):
    if ids in session:
        if request.form["select1"] == "Choose Course":
            return render_template('sign_up_form.html', data="*Please Select a Course  :(")
            # print(request.form['options'],len(request.form),ids)
        elif request.form["date"] == "":
            return render_template('sign_up_form.html', data="*Date of Birth not Valid  :(")

        elif isValid(request.form["parant_mob"]) == None:
            return render_template('sign_up_form.html', data="*Parent contact number not valid  :(")

        elif isValid(request.form["std_mob"]) == None:
            return render_template('sign_up_form.html', data="*Student contact number not valid  :(")

        else:
            response = db_operation.saving_form_info(request.form, ids)
            if response == 1:
                return redirect(url_for('home', ids=ids))
            elif response == "already user in db":
                return render_template('sign_up_form.html', data="*ERROR!. Please Contact to the Admin  :(")
            else:
                return render_template('sign_up_form.html', data="*Internal Server Error, Sorry for Inconvinience  :(")

    else:
        return "Not Authorize User"


@app.route("/logout/<ids>", methods=["GET"])
def logout(ids):
    session.pop(str(ids), None)
    return redirect(url_for('home', ids=None))


# -------------------------------------------------API----------------------------------------------------------
@app.route('/index/<ids>/index_data', methods=["GET"])
@app.route('/index/index_data', methods=["GET"])
def index_data(ids=None):
    return {"courses": db_operation.index_page()}, 200


@app.route('/course/<ids>/course_data', methods=["GET"])
@app.route('/course/course_data', methods=["GET"])
def course_data(ids=None):
    return {"courses": db_operation.index_page()}, 200


@app.route('/my_courses/my_courses_data', methods=["GET"])
@app.route('/my_courses/<ids>/my_courses_data', methods=["GET"])
def my_courses_data(ids=None):
    if session.get(ids) == None:
        return {"courses": 0}, 200
    else:
        return {"courses": db_operation.my_courses(ids)}, 200


@app.route('/course_details/<ids>/courses_details_data', methods=["GET"])
@app.route('/course_details/courses_details_data', methods=["GET"])
def course_details_data(ids=None):
    if request.args:
        args = request.args
        return jsonify({"courses": db_operation.courses_details_data(args["data"])}), 200
    else:
        return jsonify({"courses": 0}), 200



'''
@app.route('/<temp1>/<temp2>/footer',methods=["GET"])
@app.route('/footer',methods=["GET"])
def index_data(temp1=None,temp2=None):

    return jsonify({"message": "OKjskdhfjshf"}, 200)
'''

# --------------------------------------=========All Moduel=====-------------------------------------


def isValid(s):
    Pattern=re.compile("(0/91)?[6-9][0-9]{9}")
    return Pattern.match(s)


if __name__ == "__main__":
  #  socketio.run(app,ssl_context=('cert.pem', 'key.pem'),host='192.168.43.192', debug=True)
    # socketio.run(app,ssl_context=('cert.pem', 'key.pem'),host='192.168.225.24', debug=True)

   # socketio.run(app,ssl_context=('cert.pem', 'key.pem'),host='192.168.1.67', debug=True)
    # socketio.run(app,ssl_context=('cert.pem', 'key.pem'),host='127.0.0.1', debug=True)

    socketio.run(app, host='127.0.0.1', ssl_context="adhoc", debug=True)
