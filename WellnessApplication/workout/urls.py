from django.urls import path 
from .views import RecommendProgram


app_name = 'workout'
urlpatterns=[
    path('recommend/', RecommendProgram.as_view(), name='recommend_program'),
]