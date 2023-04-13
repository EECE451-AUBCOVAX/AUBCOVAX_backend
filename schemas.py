from marshmallow import Schema
from database import User


class UserSchema(Schema):
    class Meta:
        fields = ("user_name", "role", "first_name", "last_name", "email", "phone_number", "city", "country", "medical_conditions", "date_of_birth", "id_card")
        model = User


user_schema=UserSchema()
users_schema=UserSchema(many=True)