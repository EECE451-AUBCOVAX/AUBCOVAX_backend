from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import abort
import jwt
import datetime
from dotenv import load_dotenv
import os

from database import  bcrypt, db, User
from schemas import  user_schema, users_schema

import random
import string



app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_CONFIG")

db.app = app
db.init_app(app)
bcrypt.init_app(app)

SECRET_KEY = "b'|\xe7\xbfU3`\xc4\xec\xa7\xa9zf:}\xb5\xc7\xb9\x139^3@Dv'"


@app.route('/', methods=['GET'])
def hello_world():
 return "This is our Web App for EECE 451. Credits to: Jad Moukaddam, Ali Jaafar, Sarah Khalifeh, and Marwa Al Hakim"

def check_field(request, field, max_length):
    if (request.json.get(field) is None):
        return jsonify([f"Missing header {field}"]), 400
    if (request.json[field]=="" or request.json[field]==None):
        return jsonify([f"Failed to create resource ({field} should not be empty header)"]), 400
    if (max_length != -1 and len(request.json[field])>max_length):
        return jsonify([f"Failed to create resource ({field} length too long)"]), 400
    if (type(request.json[field]) == str and request.json[field].isalnum()==False):
        return jsonify([f"Failed to create resource ({field} name must be alphanumeric)"]), 400

@app.route('/user', methods=['POST'])
def Create_User():
    # Check if the request is valid
    check_field(request, "user_name", 30)
    check_field(request, "password", 128)
    check_field(request, "first_name", 30)
    check_field(request, "last_name", 30)
    check_field(request, "email", 30)
    check_field(request, "phone_number", 30)
    check_field(request, "city", 30)
    check_field(request, "country", 30)
    check_field(request, "medical_conditions", 200)
    check_field(request, "date_of_birth", 30)
    check_field(request, "id_card", -1)
    
    # Check if the user already exists
    user = User.query.filter_by(user_name=request.json["user_name"]).first()
    if user:
        return jsonify([f"Failed to create resource (username {user.user_name} already exists)"]), 409
    user = User.query.filter_by(email=request.json["email"]).first()
    if user:
        return jsonify([f"Failed to create resource (email {user.email} already exists)"]), 409
    user = User.query.filter_by(phone_number=request.json["phone_number"]).first()
    if user:
        return jsonify([f"Failed to create resource (phone number {user.phone_number} already exists)"]), 409
    user = User.query.filter_by(id_card=request.json["id_card"]).first()
    if user:
        return jsonify([f"Failed to create resource (id_card {user.id_card} already exists)"]), 409


    u=User(user_name=request.json["user_name"],password=request.json["password"], first_name=request.json["first_name"], 
           last_name=request.json["last_name"], email=request.json["email"], phone_number=request.json["phone_number"], 
           city=request.json["city"], country=request.json["country"], medical_conditions=request.json["medical_conditions"], 
           date_of_birth=datetime.datetime.strptime(request.json["date_of_birth"],'%Y-%m-%d').date(), id_card=request.json["id_card"])
    db.session.add(u)
    db.session.commit()
    return jsonify(user_schema.dump(u)), 201


@app.route('/authentication', methods=['POST'])
def Authenticate_User():
    if (not request.json.get("user_name") or not request.json.get("password")):
        abort(400)
    
    user = User.query.filter_by(user_name=request.json["user_name"]).first()
    if user is None:
        abort(403)

    
    if not bcrypt.check_password_hash(user.hashed_password, request.json["password"]):
        abort(403)

    
    return jsonify({"token": create_token(user.id), "role": user.role}), 200

@app.route('/check_token', methods=['POST'])
def check_token():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            return jsonify({"user_id": user_id}), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)

    abort(403)

@app.route("/generate_personel", methods=["POST"])
def generate_personel():
    randUser = ''.join(random.choices(string.ascii_lowercase, k=7))
    passw = "1234"
    while(User.query.filter_by(user_name=randUser).first() is not None):
        randUser = ''.join(random.choices(string.ascii_lowercase, k=7))
    
    randPhone = ''.join(random.choices(string.digits, k=8))
    while(User.query.filter_by(phone_number=randPhone).first() is not None):
        randPhone = ''.join(random.choices(string.digits, k=8))
    
    u=User(user_name=randUser,password=passw, first_name=randUser,
              last_name=randUser, email=randUser+"@personel.com", phone_number="", 
              city="Beirut", country="Lebanon", medical_conditions="None", 
              date_of_birth=datetime.datetime.strptime("2000-01-01",'%Y-%m-%d').date(), id_card="00000000")
    
    db.session.add(u)
    db.session.commit()
    return jsonify(user_schema.dump(u)), 201

@app.route("/users", methods=["GET"])
def get_users():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            if (User.query.get(user_id).role != "admin"):
                abort(403)
            users = User.query.filter(User.role != "admin")
            return jsonify(users_schema.dump(users)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    
@app.route("/generate_admin", methods=["POST"])
def generate_admin():
    if (User.query.filter_by(user_name="admin").first() is not None):
        abort(409)
    user=User(user_name="admin",password="admin", first_name="admin",
              last_name="admin", email="admin@example.com", phone_number="0000000000",
                city="admin", country="admin", medical_conditions="admin",
                date_of_birth=datetime.datetime.strptime("2020-01-01",'%Y-%m-%d').date(), id_card=000, role="admin")
    db.session.add(user)
    db.session.commit()
    return jsonify(user_schema.dump(user)), 201


@app.route("/user/phone", methods=["GET"])
def get_user_by_phone_number():
    phone_number = request.args.get("number")
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            if (User.query.get(user_id).role == "user"):
                abort(403)
            user = User.query.filter_by(phone_number=phone_number).filter(User.role == "user").first()
            return jsonify(user_schema.dump(user)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)


@app.route("/user", methods=["GET"])
def get_user():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            return jsonify(user_schema.dump(user)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)

@app.route("/user/personel", methods=["GET"])
def get_user_personel():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user.role != "admin"):
                abort(403)
            personel = User.query.filter(User.role == "personel")
            return jsonify(users_schema.dump(personel)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)

def extract_auth_token(authenticated_request):
    auth_header = authenticated_request.headers.get('Authorization')
    if auth_header:
        print("passed")
        return auth_header.split(" ")[1]
    else:
        return None

def decode_token(token):
    payload = jwt.decode(token, SECRET_KEY, 'HS256')
    return payload['sub']

def create_token(user_id):
    payload = {
    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=4),
    'iat': datetime.datetime.utcnow(),
    'sub': user_id
    }
    return jwt.encode(
    payload,
    SECRET_KEY,
    algorithm='HS256'
    )


CORS(app)

if __name__ == '__main__':
    app.run(debug=True)