from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from phonenumber_field.validators import validate_international_phonenumber


def validate_user_fields(user):
    email = user.get("email")
    name = user.get("name")
    phone = user.get("phone")
    username = user.get("username")

    if name is None or phone is None or username is None:
        raise ValidationError(message="name and phone are required fiels")

    try:
        validate_email(email)
    except ValidationError as e:
        raise ValidationError(message="Invalid email")

    try:
        validate_international_phonenumber(phone)
    except Exception:
        raise ValidationError(message="Invalid phone number")
