from marshmallow import Schema
from database import User


class UserSchema(Schema):
    class Meta:
        fields = ("id", "user_name", "role")
        model = User


user_schema=UserSchema()
users_schema=UserSchema(many=True)