# urls.py
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('encrypt/', views.encrypt, name='encrypt'),
    re_path(r'^decrypt/(?P<hex_code>[a-fA-F0-9]+)/$', views.decrypt, name='decrypt'),
]