from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, smart_str
from django.core.mail import send_mail
from django.urls import reverse

from .forms import RegisterForm
from .models import Profile
from .tokens import generate_token
from products.utils import send_verification_email

def registration(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username= form.cleaned_data['username'],
                email= form.cleaned_data['email'],
                password= form.cleaned_data['password'],
                is_active = False
            )
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = generate_token.make_token(user)
            # link = f"http://127.0.0.1:8000/accounts/verify/{uid}/{token}/"
            verify_url = request.build_absolute_uri(
                    reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
                )
            
            # send_mail(
            #     'Verify your Email',
            #     f'Click the link to verify: {verify_url}',
            #     'skdsadhon@gmail.com',
            #     [user.email],
            # )
            send_verification_email(user, verify_url) 
            messages.success(request, "Check you email to verify account")
            return redirect('login')
    else:
            form = RegisterForm()
    return render(request, 'accounts/registration.html', {'form': form})
    
def verify_email(request, uidb64, token):
    context = {'success': False}
    try:
        uid = smart_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        messages.error(request, "Invalid verification link")
        return render(request, 'accounts/verify_email.html', context)
    
    if generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        
        if hasattr(user, 'profile'):
            user.profile.is_email_verified = True
            user.profile.save()
            
        context["success"] = True
        messages.success(request, "Email verified successfully")
    else:
        messages.error(request, "Verification link expired or invalid")
    return render(request, 'accounts/verify_email.html', context)


    

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(username = username, password = password)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.is_email_verified:
                login(request, user, backend= 'django.contrib.auth.backends.ModelBackend',)
                return redirect('home')
            else:
                messages.error(request, "Verify email first!")
        else:
            messages.error(request, "Invalid credentials")
    
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')