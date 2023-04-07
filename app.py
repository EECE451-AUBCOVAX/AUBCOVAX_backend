from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import abort
import jwt
import datetime
from dotenv import load_dotenv
import os

from database import  bcrypt, db, User
from schemas import  user_schema, users_schema

app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_CONFIG")

db.app = app
db.init_app(app)
bcrypt.init_app(app)

SECRET_KEY = "b'|\xe7\xbfU3`\xc4\xec\xa7\xa9zf:}\xb5\xc7\xb9\x139^3@Dv'"


@app.route('/hello', methods=['GET'])
def hello_world():
 return "Hello World!"


@app.route('/user', methods=['POST'])
def Create_User():
    # Check if the request is valid
    if (request.json.get("user_name") is None or request.json.get("password") is None):
        return jsonify(["Missing headers"]), 400
    if (request.json["user_name"]=="" or request.json["password"]=="" or request.json["user_name"]==None or request.json["password"]==None):
        return jsonify(["Failed to create resource (One or more empty headers)"]), 400
    if (len(request.json["user_name"])>30 or len(request.json["password"])>128):
        return jsonify(["Failed to create resource (One or more headers are too long)"]), 400
    if (User.query.filter_by(user_name=request.json["user_name"]).first() is not None):
        return jsonify(["Failed to create resource (User already exists)"]), 400
    if (request.json["user_name"].isalnum()==False):
        return jsonify(["Failed to create resource (User name must be alphanumeric)"]), 400
    if (request.json["password"].isalnum()==False):
        return jsonify(["Failed to create resource (Password must be alphanumeric)"]), 400
    
    u=User(request.json["user_name"],request.json["password"])
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


    return jsonify({"token": create_token(user.id)}), 200

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