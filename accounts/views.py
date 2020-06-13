from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters

from accounts.models import User
from accounts.serializers import UserViewSetSerializer


class GetAllUsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserViewSetSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering = '-id'

