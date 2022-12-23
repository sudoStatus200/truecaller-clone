from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    phone = models.CharField(max_length=15, null=False)
    email = models.EmailField(max_length=100, null=True)
    name = models.CharField(max_length=100, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=15, null=False)
    spam_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.phone)


class ContactsMapping(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=False)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("contact", "account")

    def __str__(self):
        return str(self.account) + "," + str(self.contact)
