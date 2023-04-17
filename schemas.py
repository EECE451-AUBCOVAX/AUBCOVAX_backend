from marshmallow import Schema
from database import User, Reservation


class UserSchema(Schema):
    class Meta:
        fields = ("user_name", "role", "first_name", "last_name", "email", "phone_number", "city", "country", "medical_conditions", "date_of_birth", "id_card")
        model = User


user_schema=UserSchema()
users_schema=UserSchema(many=True)

class ReservationSchema(Schema):
    class Meta:
        fields = ("personel", "patient", "date", "time", "status")
        model = Reservation

reservation_schema=ReservationSchema()
reservations_schema=ReservationSchema(many=True)

class LimitedReservationSchema(Schema):
    class Meta:
        fields = ("personel","patient","data","status")
        model = Reservation

limited_reservation_schema=LimitedReservationSchema()
limited_reservations_schema=LimitedReservationSchema(many=True)