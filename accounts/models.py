from django.db import models
from django.contrib.auth.models import AbstractUser
import jsonfield

# Create your models here.


class UserDetails(models.Model):
    date_of_birth = models.DateField()
    mobile_no = models.IntegerField()
    extra_phone = jsonfield.JSONField(null=True)


class User(AbstractUser):
    user_details = models.OneToOneField(UserDetails, null=True, on_delete=models.SET_NULL)
    pass

