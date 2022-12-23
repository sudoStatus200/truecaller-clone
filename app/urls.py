from django.urls import path
from app import views

urlpatterns = [
    path("signup", views.Signup.as_view()),
    path("login", views.Login.as_view()),
    path("spam", views.Spam.as_view()),
    path("search_name", views.SearchName.as_view()),
    path("search_phone", views.SearchPhone.as_view()),
    path("get_user", views.GetUser.as_view()),
    path("upload_contacts", views.UploadContacts.as_view())
]
