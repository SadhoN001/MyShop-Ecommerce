from django.urls import path
from .views import registration, verify_email, user_login, user_logout

urlpatterns =[
    path('register/', registration, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('verify/<uidb64>/<token>/', verify_email, name='verify_email'),
]