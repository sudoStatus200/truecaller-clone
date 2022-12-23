import environ
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Account, Contact, ContactsMapping, User
import jwt
import json
from django.contrib.auth import authenticate
from rest_framework.authentication import get_authorization_header, BaseAuthentication
from rest_framework import exceptions
from .validators import validate_user_fields
from django.core.exceptions import ValidationError
from django.db.models import Q


env = environ.Env()

JWT_SECRET_KEY = env("JWT_SECRET_KEY")

# Create your views here.


class Signup(APIView):
    def post(self, request):
        try:
            username = request.data.get("username", None)
            name = request.data.get("name", None)
            password = request.data.get("password", None)
            email = request.data.get("email", None)
            phone = request.data.get("phone", None)

            user_object = {
                "name": name,
                "username": username,
                "email": email,
                "phone": phone,
            }

            validate_user_fields(user_object)

            user = User(username=username, password=password, email=email)

            user.set_password(password)

            account = Account(user=user, phone=phone, email=email, name=name)

            contact = Contact(account=account, phone=phone, name=name)

            user.save()
            account.save()
            contact.save()

            payload = {
                "id": user.id,
                "username": user.username,
            }

            response = {
                "token": jwt.encode(
                    payload,
                    JWT_SECRET_KEY,
                    algorithm="HS256",
                ),
                "id": account.id,
            }

            return Response(response, status=200, content_type="application/json")

        except ValidationError as e:
            print(e)
            return Response(
                {"message": e.message},
                status=400,
                content_type="application/json",
            )

        except Exception as e:
            print(e)
            return Response(
                {"message": "Internal server error"},
                status=500,
                content_type="application/json",
            )


class Login(APIView):
    def post(self, request):
        try:
            if not request.data:
                raise ValidationError(message="Please provide username/password")

            username = request.data.get("username", None)
            password = request.data.get("password", None)

            if not username or not password:
                raise ValidationError(message="Please provide username/password")

            if authenticate(username=username, password=password):
                user = User.objects.get(username=username)
            else:
                return Response({"Error": "Unauthorized"}, status=401)

            if user:
                payload = {
                    "id": user.id,
                    "username": user.username,
                }

                jwt_token = {
                    "token": jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
                }

                return Response(jwt_token, status=200, content_type="application/json")
            else:
                return Response(
                    json.dumps({"Error": "Unauthorized"}),
                    status=401,
                    content_type="application/json",
                )

        except ValidationError as e:
            return Response(
                {"message": e.message},
                status=400,
                content_type="application/json",
            )

        except Exception as e:
            return Response(
                {"message": "Internal server error"},
                status=500,
                content_type="application/json",
            )


class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b"bearer":
            return ("", {"Error": "Token is invalid"})

        if len(auth) == 1 or len(auth) > 2:
            msg = "Invalid token header"
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1]
            if token == "null":
                msg = "Null token not allowed"
                raise exceptions.AuthenticationFailed(msg)
        except UnicodeError:
            msg = "Invalid token header. Token string should not contain invalid characters."
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=["HS256"],
            )
            username = payload["username"]
            userid = payload["id"]
            user = User.objects.get(username=username, id=userid, is_active=True)
        except Exception as e:
            return ("", {"Error": "Token is invalid"})

        return (user, "")


class SearchName(APIView):
    def get(self, request):
        try:
            auth = TokenAuthentication()

            user, error = auth.authenticate(request)

            if error:
                raise exceptions.AuthenticationFailed(detail="Unauthorized", code=401)
            else:
                name = request.GET.get("name", None)

                exact_match = Contact.objects.filter(name=name).all()

                shallow_match = (
                    Contact.objects.filter(name__contains=name)
                    .filter(~Q(name=name))
                    .all()
                )
                response = []
                for match in exact_match:
                    response.append(
                        {
                            "name": match.name,
                            "phone": match.phone,
                            "spam_count": match.spam_count,
                        }
                    )
                for match in shallow_match:
                    response.append(
                        {
                            "name": match.name,
                            "phone": match.phone,
                            "spam_count": match.spam_count,
                        }
                    )
                return Response(response, status=200, content_type="application/json")
        except exceptions.AuthenticationFailed as e:
            return Response(
                {"Error": e.detail},
                status=401,
                content_type="application/json",
            )

        except Exception as e:
            print(e)
            return Response(
                {"Error": "Internal server error"},
                status=500,
                content_type="application/json",
            )


class SearchPhone(APIView):
    def get(self, request):
        phone = request.GET.get("phone", None)

        try:
            auth = TokenAuthentication()
            _, error = auth.authenticate(request)

            if error:
                raise exceptions.AuthenticationFailed(detail="Unauthorized")
            else:
                account = Account.objects.get(phone=phone)
                contact = Contact.objects.get(phone=phone)
                response = {
                    "name": account.name,
                    "phone": account.phone,
                    "spam_count": contact.spam_count,
                }

                return Response(response, status=200, content_type="application/json")

        except Account.DoesNotExist:
            contact_info = Contact.objects.get(phone=phone)
            response = []

            for contact in contact_info:
                response.append(
                    {
                        "name": contact_info.name,
                        "phone": contact_info.phone,
                        "spam_count": contact_info.spam_count,
                    }
                )

            return Response(response, status=200, content_type="application/json")

        except exceptions.AuthenticationFailed as e:
            return Response(
                {"Error": "Unauthorized"},
                status=401,
                content_type="application/json",
            )

        except:
            return Response(
                json.dumps({"Error": "Internal server error"}),
                status=500,
                content_type="application/json",
            )


class Spam(APIView):
    def post(self, request):
        try:
            auth = TokenAuthentication()
            _, error = auth.authenticate(request)
            if error:
                return Response(error, status=401, content_type="application/json")
            else:
                phone = request.data.get("phone", None)
                try:
                    contact = Contact.objects.get(phone=phone)
                    _ = Contact.objects.filter(phone=phone).update(
                        spam_count=contact.spam_count + 1
                    )

                except Contact.DoesNotExist:
                    print(phone)
                    _ = Contact(spam_count=1, phone=phone).save()

                return Response(
                    {"message": "success"},
                    status=200,
                    content_type="application/json",
                )

        except Exception as e:
            print(e)
            return Response(
                {"Error": "Internal server error"},
                status=500,
                content_type="application/json",
            )


class GetUser(APIView):
    def get(self, request):
        try:
            auth = TokenAuthentication()
            user, error = auth.authenticate(request)
            if error:
                return Response(error, status=401, content_type="application/json")
            else:
                user_account_id = Account.objects.get(user=user)
                contact_id = request.GET.get("contact_id", None)
                contact_info = Contact.objects.get(id=contact_id)

                email = None
                if contact_info.account:
                    contact_map = ContactsMapping.objects.filter(
                        account_id=user_account_id, contact_id=contact_id
                    ).all()

                    account = Account.objects.get(id=contact_info.account_id)

                    if len(contact_map) > 0:
                        email = account.email

                    return Response(
                        {
                            "name": account.name,
                            "phone": account.phone,
                            "email": email,
                            "spam_count": contact_info.spam_count,
                        },
                        status=400,
                        content_type="application/json",
                    )
                else:

                    return Response(
                        {
                            "name": contact_info.name,
                            "phone": contact_info.phone,
                            "email": email,
                            "spam_count": contact_info.spam_count,
                        },
                        status=400,
                        content_type="application/json",
                    )

        except Contact.DoesNotExist:
            return Response(
                {"Error": "Contact does not exits"},
                status=400,
                content_type="application/json",
            )

        except Exception as e:
            print(e)
            return Response(
                {"Error": "Internal server error"},
                status=500,
                content_type="application/json",
            )


"""
This is just for seeding and testing purpose hence made it public 
"""


class UploadContacts(APIView):
    def post(self, request):
        try:

            data = request.data.get("contacts", None)

            for val in data:
                name = val.get("name")
                account_id = val.get("account_id")
                phone = val.get("phone")
                contacts = Contact.objects.all().filter(phone=phone, name=name)
                contact_id = None
                if len(contacts) > 0:
                    contact_id = contacts[0].id
                else:
                    contact_info = Contact(
                        phone=phone, account_id=account_id, name=name
                    )
                    contact_info.save()
                    contact_id = contact_info.id

                ContactsMapping(
                    contact_id=contact_id, account_id=account_id, name=name
                ).save()

            return Response(
                {"message": "success"},
                status=200,
                content_type="application/json",
            )

        except Exception as e:
            print(e)
            return Response(
                {"Error": "Internal server error"},
                status=500,
                content_type="application/json",
            )
