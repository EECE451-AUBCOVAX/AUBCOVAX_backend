from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {'schema': 'aubcovax'}
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(30), unique=True)
    hashed_password = db.Column(db.String(128))
    role = db.Column(db.String(30), default="user")
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    email = db.Column(db.String(30), unique=True)
    phone_number = db.Column(db.String(30), unique=True)
    city = db.Column(db.String(30))
    country = db.Column(db.String(30))
    medical_conditions = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    id_card = db.Column(db.Integer, unique=True)

    def __init__(self, user_name, password, first_name, last_name, email, phone_number, city, country, medical_conditions, date_of_birth, id_card, role="user"):
        super(User, self).__init__(user_name=user_name)
        self.hashed_password = bcrypt.generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone_number = phone_number
        self.city = city
        self.country = country
        self.medical_conditions = medical_conditions
        self.date_of_birth = date_of_birth
        self.id_card = id_card
        self.role = role

        

class Reservation(db.Model):
    __tablename__ = "reservations"
    __table_args__ = {'schema': 'aubcovax'}
    id = db.Column(db.Integer, primary_key=True)
    personel = db.Column(db.String(30), db.ForeignKey("aubcovax.users.user_name"))
    patient = db.Column(db.String(30), db.ForeignKey("aubcovax.users.user_name"))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    status = db.Column(db.String(30), default="pending")

    def __init__(self, Patient, Personel, date, time, status="pending"):
        super(Reservation, self).__init__(patient=Patient, personel=Personel, date=date, time=time, status=status)
