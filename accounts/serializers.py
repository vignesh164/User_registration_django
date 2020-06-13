from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

try:
    from allauth.account import app_settings as allauth_settings
    from allauth.utils import (email_address_exists,
                               get_username_max_length)
    from allauth.account.adapter import get_adapter
    from allauth.account.utils import setup_user_email
    from allauth.socialaccount.helpers import complete_social_login
    from allauth.socialaccount.models import SocialAccount
    from allauth.socialaccount.providers.base import AuthProcess
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")

from rest_framework import serializers
from requests.exceptions import HTTPError
from rest_auth.serializers import UserDetailsSerializer

from .models import UserDetails, User


class UserExtraDetailsSerializer(serializers.ModelSerializer):
    extra_phone = serializers.JSONField()

    class Meta:
        model = UserDetails
        fields = ('date_of_birth', 'mobile_no', 'extra_phone')


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=get_username_max_length(),
        min_length=allauth_settings.USERNAME_MIN_LENGTH,
        required=allauth_settings.USERNAME_REQUIRED
    )
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    user_details = UserExtraDetailsSerializer(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."))
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'user_details': self.validated_data.get('user_details', '')
        }

    def save(self, request):
        adapter = get_adapter()
        self.cleaned_data = self.get_cleaned_data()

        try:
            user_details = dict(self.cleaned_data['user_details'])
            user_details = UserDetails.objects.create(**user_details)
        except Exception as E:
            raise serializers.ValidationError(_("Problem while creating user details " + str(E)))

        user = adapter.new_user(request)
        adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        user.user_details = user_details
        user.save()
        return user


class UserSerializer(UserDetailsSerializer):
    user_details = UserExtraDetailsSerializer()

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('user_details',)

    def update(self, instance, validated_data):
        extra_user_details = validated_data.pop('user_details', None)
        instance = super(UserSerializer, self).update(instance, validated_data)
        instance.user_details.date_of_birth = extra_user_details['date_of_birth']
        instance.user_details.mobile_no = extra_user_details['mobile_no']
        instance.user_details.extra_phone = extra_user_details['extra_phone']
        instance.save()
        return instance


class UserViewSetSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(source='user_details.date_of_birth')
    mobile_no = serializers.CharField(source='user_details.mobile_no')
    extra_phone = serializers.JSONField(source='user_details.extra_phone')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'date_of_birth', 'email', 'mobile_no', 'extra_phone',)
