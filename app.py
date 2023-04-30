from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask import abort
import jwt
import datetime
from dotenv import load_dotenv
import os

from database import  bcrypt, db, User, Reservation
from schemas import  user_schema, users_schema, reservation_schema, reservations_schema, light_user_schema, personel_schema, personels_schema

import random
import string
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.generic import AnnotationBuilder
from smtplib import SMTPRecipientsRefused
from validate_email_address import validate_email
import subprocess
from io import StringIO
from time import sleep
import platform

systemversion = platform.system()

def get_pdf_name():
    if (systemversion == "Windows"):
        return "output"
    else:
        return "texput"


# Set up the email message

smtp_username = "noreply.covaxaub@gmail.com"
subject = "Vaccination appointment"

time_format='%H:%M'
date_format='%Y-%m-%d'

CERTIFICATE_TEMPLATE="\\documentclass{article}\\usepackage{graphicx}\\begin{document}\\pagestyle{empty}\\begin{figure}[h!]  \\centering  \\includegraphics[width=1\\textwidth,height=0.4\\textheight]{./AUBCMC.png}  \\label{fig:example}\\end{figure}\\begin{center}  {\\huge\\bfseries\\mbox{COVID-19 Vaccination Certificate}} \\\\[40pt]\\begin{tabular}{ll}    \\fontsize{15}{14}\\selectfont Name: &\\fontsize{15}{14}\\selectfont %s\\\\[15pt]\\fontsize{15}{14}\\selectfont Date of birth: &\\fontsize{15}{14}\\selectfont %s\\\\[15pt]\\fontsize{15}{14}\\selectfont 1st vaccine: &\\fontsize{15}{14}\\selectfont %s\\\\[15pt]\\fontsize{15}{14}\\selectfont 2nd vaccine: &\\fontsize{15}{14}\\selectfont %s\\\\[15pt]\\end{tabular}\\end{center}\\end{document}"

app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_CONFIG")

db.app = app
db.init_app(app)
bcrypt.init_app(app)

SECRET_KEY = "b'|\xe7\xbfU3`\xc4\xec\xa7\xa9zf:}\xb5\xc7\xb9\x139^3@Dv'"
def send_email(to_address, body):
    msg = f"Subject: {subject}\n\n{body}"
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(smtp_username, os.getenv("mailpassword"))
            smtp.sendmail(smtp_username, to_address, msg)
    except SMTPRecipientsRefused:
        return False

@app.route('/', methods=['GET'])
def hello_world():
 return "This is our Web App for EECE 451. Credits to: Jad Moukaddam, Ali Jaafar, Sarah Khalifeh, and Marwa Al Hakim"

def check_field(request, field, max_length):
    if (request.json.get(field) is None):
        return jsonify({"message":f"Missing header {field}"}), 400
    if (request.json[field]=="" or request.json[field]==None):
        return jsonify({"message":f"Failed to create resource ({field} should not be empty header)"}), 400
    if (max_length != -1 and len(request.json[field])>max_length):
        return jsonify({"message":f"Failed to create resource ({field} length too long)"}), 400
    if (type(request.json[field]) == str and request.json[field].isalnum()==False):
        return jsonify({"message":f"Failed to create resource ({field} name must be alphanumeric)"}), 400

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
    
    if (not validate_email(request.json["email"])):
        return jsonify({"message": f"Failed to create resource (invalid email: {request.json['email']})"}), 400
    # Check if the user already exists
    user = User.query.filter_by(user_name=request.json["user_name"]).first()
    if user:
        return jsonify({"message":f"Failed to create resource (username {user.user_name} already exists)"}), 409
    user = User.query.filter_by(email=request.json["email"]).first()
    if user:
        return jsonify({"message":f"Failed to create resource (email {user.email} already exists)"}), 409
    user = User.query.filter_by(phone_number=request.json["phone_number"]).first()
    if user:
        return jsonify({"message":f"Failed to create resource (phone number {user.phone_number} already exists)"}), 409
    user = User.query.filter_by(id_card=request.json["id_card"]).first()
    if user:
        return jsonify({"message":f"Failed to create resource (id_card {user.id_card} already exists)"}), 409


    u=User(user_name=request.json["user_name"],password=request.json["password"], first_name=request.json["first_name"], 
           last_name=request.json["last_name"], email=request.json["email"], phone_number=request.json["phone_number"], 
           city=request.json["city"], country=request.json["country"], medical_conditions=request.json["medical_conditions"], 
           date_of_birth=datetime.datetime.strptime(request.json["date_of_birth"],date_format).date(), id_card=request.json["id_card"])
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

@app.route("/reservations", methods=["GET"])
def get_reservations():
    reservations = Reservation.query.order_by(Reservation.date).order_by(Reservation.time).all()
    return jsonify(reservations_schema.dump(reservations)), 200

@app.route("/generate_personel", methods=["POST"])
def generate_personel():
    randUser = ''.join(random.choices(string.ascii_lowercase, k=7))
    passw = "1234"
    while(User.query.filter_by(user_name=randUser).first() is not None):
        randUser = ''.join(random.choices(string.ascii_lowercase, k=7))
    
    randPhone = ''.join(random.choices(string.digits, k=8))
    while(User.query.filter_by(phone_number=randPhone).first() is not None):
        randPhone = ''.join(random.choices(string.digits, k=8))

    randId = ''.join(random.choices(string.digits, k=8))
    while(User.query.filter_by(id_card=randId).first() is not None):
        randId = ''.join(random.choices(string.digits, k=8))
    
    user=User(user_name=randUser,password=passw, first_name=randUser,
              last_name=randUser, email=randUser+"@personel.com", phone_number=randPhone, 
              city="Beirut", country="Lebanon", medical_conditions="None", 
              date_of_birth=datetime.datetime.strptime("2000-01-01",date_format).date(), id_card=randId)
    user.role="personel"
    db.session.add(user)
    db.session.commit()
    return jsonify(user_schema.dump(user)), 201

@app.route("/users", methods=["GET"])
def get_users():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user=User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role != "admin"):
                abort(403)
            users = User.query.filter(User.role != "admin")
            return jsonify(users_schema.dump(users)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
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
            user=User.query.get(user_id)
            if (user is None):
                abort(404)
            if ( user.role== "user"):
                abort(403)
            user = User.query.filter_by(phone_number=phone_number).filter(User.role == "user").first()
            return jsonify(light_user_schema.dump(user)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)


@app.route("/user", methods=["GET"])
def get_user():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(404)
            return jsonify(user_schema.dump(user)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

@app.route("/user/personel", methods=["GET"])
def get_user_personel():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role != "admin"):
                abort(403)
            personel = User.query.filter(User.role == "personel")
            if (personel is None):
                abort(404)
            if (personel.count() == 1):
                return jsonify(personel_schema.dump(personel.first())), 200
            return jsonify(personels_schema.dump(personel)), 200
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

@app.route("/user/patient", methods=["GET"])
def get_user_patient():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role != "admin" and user.role!="personel"):
                abort(403)
            users = User.query.filter(User.role == "user")
            return jsonify(users_schema.dump(users)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

@app.route("/user/reserve", methods=["POST"])
def get_user_reserve():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role != "user"):
                abort(403)
            personel = User.query.filter(User.role=="personel")
            name= user.user_name
            userReservations = Reservation.query.filter(Reservation.patient == name)
            if (userReservations.count() == 0):
                reservations = Reservation.query.filter(Reservation.date > datetime.date.today()+ datetime.timedelta(13)).order_by(Reservation.date).order_by(Reservation.time)
                if (reservations.count() == 0):
                    reserve = Reservation(date=datetime.date.today()+datetime.timedelta(14), Patient=name, Personel=personel[0].user_name, time=datetime.time(8,00))
                    db.session.add(reserve)
                    db.session.commit()
                    send_email(user.email, "Your first dose reservation is confirmed. \nPlease show up on the "+str(reserve.date)+" at "+str(reserve.time))
                    return jsonify(reservation_schema.dump(reserve)), 201
                else:
                    numPersonel = personel.count()
                    date = datetime.date.today()+datetime.timedelta(14)
                    time = datetime.time(8,00)
                    numReservationsperday = 20*numPersonel
                    r=numReservationsperday-1
                    while (reservations.count()>r and reservations[r].date == date):
                        r+=numReservationsperday
                        date=date+datetime.timedelta(1)
                    slot=r-numReservationsperday+1
                    numReservationsperslot = numPersonel
                    slot+=numReservationsperslot-1
                    while (reservations.count()>slot and reservations[slot].time == time):
                        slot+=numReservationsperslot
                        time=(datetime.datetime.combine(date, time)+datetime.timedelta(minutes=30)).time()
                    reservationAtSlot = Reservation.query.filter(Reservation.date == date).filter(Reservation.time == time)
                    personelNames = []
                    for p in personel:
                        personelNames.append(p.user_name)
                    for reserv in reservationAtSlot:
                        personelNames.remove(reserv.personel)
                    reservation=Reservation(date=date, Patient=name, Personel=personelNames[0], time=time)
                    db.session.add(reservation)
                    db.session.commit()
                    send_email(user.email, "Your first dose reservation is confirmed. \nPlease show up on the "+str(date)+" at "+str(time))
                    return jsonify(reservation_schema.dump(reservation)), 201
            else:
                return jsonify({"message":"User already has taken his first dose"}), 400
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

@app.route("/personel/reserve", methods=["POST"])
def get_personel_reserve():
    if (extract_auth_token(request) is not None):
        try:
            personel_id = decode_token(extract_auth_token(request))
            personel = User.query.get(personel_id)
            if (personel is None):
                abort(403)
            if (personel.role != "personel"):
                abort(403)
            if (request.json is None or request.json.get('patient') is None or request.json.get('date') is None 
                or request.json.get('time') is None):
                return jsonify({"message":"Missing arguments"}), 400
            patient = request.json['patient']
            confirmedReservations = Reservation.query.filter(Reservation.patient == patient).filter(Reservation.status=="confirmed")
            userReservations = Reservation.query.filter(Reservation.patient == patient)
            if (userReservations.count() == 0 or confirmedReservations.count() == 0):
                return jsonify({"message":"Patient has not taken his first dose yet, or has taken his second dose"}), 400
            if (confirmedReservations.count() > 1):
                return jsonify({"message":"Patient has already taken his second dose"}), 400
            if (userReservations.count() > 1):
                return jsonify({"message":"Patient already has an appointment for his second dose"}), 400
            user = User.query.filter(User.user_name == patient).first()
            if (user is None):
                abort(403)

            date=request.json.get('date')
            time=request.json.get('time')
            Date = datetime.datetime.strptime(date, date_format).date()
            Time = datetime.datetime.strptime(time, time_format).time()
            if (Date < datetime.date.today()+ datetime.timedelta(14)):
                return jsonify({"message":"Date is not valid (too early, needs to be at least 2 weeks away)"}), 400
            if (Time < datetime.time(8,00) or Time > datetime.time(17,30)):
                return jsonify({"message":"Time is not valid (needs to be between 8:00 and 17:30)"}), 400
            if (Time.minute != 0 and Time.minute != 30):
                return jsonify({"message":"Time is not valid (needs to be on the hour or on the half hour)"}), 400
            personelReservation = Reservation.query.filter(Reservation.personel == personel.user_name).filter(Reservation.date == Date).filter(Reservation.time == Time)
            if (personelReservation.count() != 0):
                return jsonify({"message":"Personel already has a reservation at this time"}), 400
            reservation = Reservation(date=Date, Patient=patient, Personel=personel.user_name, time=Time)
            db.session.add(reservation)
            db.session.commit()
            send_email(user.email, "Your second dose reservation is confirmed. \nPlease show up on the "+str(Date)+" at "+str(Time))
            return jsonify(reservation_schema.dump(reservation)), 201
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)

    abort(403)

@app.route("/personel/dose_confirm", methods=["POST"])
def get_personel_dose_confirm():
    if (extract_auth_token(request) is not None):
        try:
            personel_id = decode_token(extract_auth_token(request))
            personel = User.query.get(personel_id)
            if (personel is None):
                abort(403)
            if (personel.role != "personel"):
                abort(403)
            if (request.json is None or request.json.get('patient') is None or request.json.get('date') is None 
                or request.json.get('time') is None):
                return jsonify({"message":"Missing arguments"}), 400
            patient = request.json['patient']
            date=request.json.get('date')
            time=request.json.get('time')
            Date = datetime.datetime.strptime(date, date_format).date()
            Time = datetime.datetime.strptime(time, time_format).time()
            reservation = Reservation.query.filter(Reservation.patient == patient).filter(Reservation.date == Date).filter(Reservation.time == Time).first()
            if (reservation is None):
                return jsonify({"message":"No reservation found"}), 404
            #update reservation status
            reservation.status = "confirmed"
            db.session.commit()
            return jsonify(reservation_schema.dump(reservation)), 200
            
        except:
            abort(403)

@app.route("/user/certificate", methods=["GET"])
def get_certificate():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                return jsonify({"message":"User not found"}), 404
            if (user.role != "user"):
                return jsonify({"message":"User is not a patient"}), 400
            userReservations = Reservation.query.filter(Reservation.patient == user.user_name).filter(Reservation.status == "confirmed").order_by(Reservation.date).order_by(Reservation.time)
            if (userReservations.count() != 2):
                return jsonify({"message":"Patient has not taken his second dose yet, doses taken: " + userReservations.count()}), 400
            
            latex_doc = CERTIFICATE_TEMPLATE % (user.first_name+" "+user.last_name, user.date_of_birth,userReservations[0].date, userReservations[1].date)
            #print(latex_doc)
            latex_input = StringIO(latex_doc)
            # Call pdflatex with input from the StringIO object and capture the output
            #print(subprocess.run(['echo', latex_input.getvalue().encode()], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout)
            proc = subprocess.run(['pdflatex', '-jobname', "output", '-interaction', 'nonstopmode'], input=latex_input.getvalue().encode(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(user.user_name+'.pdf'):
                os.remove(user.user_name+'.pdf')
            try:
                os.rename(get_pdf_name()+".pdf", user.user_name+'.pdf')
            except:
                return jsonify({"message":"Try again in a bit"}), 429
            #print(proc.stdout.decode())
            with open(user.user_name+'.pdf', 'rb') as file:
                pdf_output = file.read()
                pdf_bytes = BytesIO(pdf_output)
                file.close()
                try:
                    
                    os.remove(get_pdf_name()+".aux")
                    os.remove(get_pdf_name()+".log")
                    os.remove(user.user_name+".pdf")
                except:
                    pass
                return send_file(pdf_bytes, download_name='certificate.pdf', as_attachment=True)
            
            
            
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

def extract_auth_token(authenticated_request):
    auth_header = authenticated_request.headers.get('Authorization')
    if auth_header:
        try:
            return auth_header.split(" ")[1]
        except IndexError:
            abort(403)
    else:
        return None

@app.route("/delete_all_reservations", methods=["DELETE"])
def delete_all_reservations():
    
    reservations = Reservation.query.all()
    for reservation in reservations:
        db.session.delete(reservation)
    db.session.commit()
    return jsonify({"message":"All reservations deleted"}), 200

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

@app.route("/personel/reservation", methods=["GET"])
def get_personel_history():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role!="personel"):
                abort(403)
            reservations = Reservation.query.filter(Reservation.personel == user.user_name).filter(Reservation.date>=datetime.datetime.today()).order_by(Reservation.date).order_by(Reservation.time)
            if (reservations.count() == 0):
                return jsonify({"message":"No reservations found"}), 400
            return jsonify(reservations_schema.dump(reservations)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

@app.route("/user/reservation", methods=["GET"])
def get_user_history():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role!="user"):
                abort(403)
            reservations = Reservation.query.filter(Reservation.patient == user.user_name).order_by(Reservation.date).order_by(Reservation.time)
            if (reservations.count() == 0):
                return jsonify({"message":"No reservations found"}), 400
            return jsonify(reservations_schema.dump(reservations)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)

@app.route("/personel/patienthistory", methods=["GET"])
def get_patient_reservation():
    if (extract_auth_token(request) is not None):
        try:
            user_id = decode_token(extract_auth_token(request))
            user = User.query.get(user_id)
            if (user is None):
                abort(403)
            if (user.role!="personel"):
                abort(403)
            patient = request.args.get("user")
            reservations = Reservation.query.filter(Reservation.patient == patient).order_by(Reservation.date).order_by(Reservation.time)
            if (reservations.count() == 0):
                return jsonify({"message":"No reservations found"}), 404
            return jsonify(reservations_schema.dump(reservations)), 200
        except jwt.ExpiredSignatureError:
            abort(403)
        except jwt.InvalidTokenError:
            abort(403)
    abort(403)



CORS(app)

if __name__ == '__main__':
    app.run(debug=True)