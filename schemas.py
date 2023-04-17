from marshmallow import Schema
from database import User, Reservation


class UserSchema(Schema):
    class Meta:
        fields = ("user_name", "role", "first_name", "last_name", "email", "phone_number", "city", "country", "medical_conditions", "date_of_birth", "id_card")
        model = User


user_schema=UserSchema()
users_schema=UserSchema(many=True)

class LightUserSchema(Schema):
    class Meta:
        fields = ("user_name", "first_name", "last_name", "email", "phone_number", "medical_conditions", "date_of_birth")
        model = User

light_user_schema=LightUserSchema()

class PersonelSchema(Schema):
    class Meta:
        fields = ("user_name", "first_name", "last_name", "email", "phone_number", "city", "country", "date_of_birth", "id_card")
        model = User

personel_schema=PersonelSchema()
personels_schema=PersonelSchema(many=True)

class ReservationSchema(Schema):
    class Meta:
        fields = ("personel", "patient", "date", "time", "status")
        model = Reservation

reservation_schema=ReservationSchema()
reservations_schema=ReservationSchema(many=True)
