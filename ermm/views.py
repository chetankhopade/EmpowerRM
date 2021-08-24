from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from app.management.utilities.functions import ok_json, bad_json, generate_token
from app.management.utilities.globals import addGlobalData

from empowerb.settings import (EMAIL_ACTIVE, EMAIL_HOST_USER, TIMEOUT_TO_ALERT_USER_SESSION,
                               TIMEOUT_TO_CLOSE_USER_SESSION)

from ermm.models import UserProfile, Company
from django.contrib.auth.decorators import login_required


@login_required(redirect_field_name='ret', login_url='/login')
def index(request):
    # ticket 362 No handling if user is not assigned to any company
    if not Company.objects.filter(usercompany__user=request.user).exists():
        return render(request, "unassigned_company.html", {'title': 'Unassigned Company'})
    return HttpResponseRedirect(reverse('companies'))


def forgot_password(request):
    data = {'title': 'Forgot Password'}
    addGlobalData(request, data)

    if request.method == 'POST':
        token = request.POST.get('token', '')
        if token:
            # Reset Password
            try:
                with transaction.atomic():
                    new_password = request.POST.get('new_password', '')
                    confirm_password = request.POST.get('confirm_password', '')

                    if not new_password:
                        return bad_json(message='New Password is required')

                    if not confirm_password:
                        return bad_json(message='Confirm Password is required')

                    if new_password != confirm_password:
                        return bad_json(message='Passwords do not match')

                    if not UserProfile.objects.filter(token=token).exists():
                        return bad_json(message='Token is invalid or corrupted')

                    my_profile = UserProfile.objects.get(token=token)

                    user = my_profile.user
                    user.set_password(new_password)
                    user.save()

                    # for security reasons we can update the token for the user profile
                    my_profile.token = generate_token()
                    my_profile.save()

                    return ok_json()

            except Exception as ex:
                return bad_json(message=ex.__str__())

        else:
            # Forgot Password
            try:
                with transaction.atomic():

                    email = request.POST.get('email', '')
                    if not email:
                        return bad_json(message='Email is required')

                    try:
                        validate_email(email)
                    except Exception:
                        return bad_json(message='Invalid email address')

                    user_by_email = User.objects.filter(email=email)
                    if not user_by_email.exists():
                        return bad_json(message='Email not registered for any user in our system')
                    else:
                        my_profile, _ = UserProfile.objects.get_or_create(user=user_by_email[0])

                    my_profile.token = generate_token()
                    my_profile.save()

                    if EMAIL_ACTIVE:
                        msg_html = render_to_string('emails/password.html', {'my_profile': my_profile}, request)
                        send_mail("Forgot Password - EmpowerRM", "", EMAIL_HOST_USER, [email], html_message=msg_html)

                    return ok_json()

            except Exception as ex:
                return bad_json(message=ex.__str__())

    # reset password (token is part of the url, if not token then is forgot password)
    data['token'] = request.GET.get('token', '')
    return render(request, "views/forgot_password.html", data)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/login")


def signup(request):
    data = {'title': 'Signup'}
    addGlobalData(request, data)
    return render(request, "views/signup.html", data)


def login_user(request):
    data = {"title": "Signin | Empower RM"}
    addGlobalData(request, data)

    if not data['user'].is_anonymous:
        return HttpResponseRedirect(reverse('companies'))

    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = authenticate(username=request.POST['email'], password=request.POST['password'])
                if user:
                    if user.is_active:
                        # Login action
                        login(request, user)

                        ret = request.POST.get('ret', '')
                        redirect_url = ret if ret else reverse('companies')
                        return ok_json(data={'redirect_url': redirect_url})
                    else:
                        return bad_json(message='Inactive User')
                else:
                    return bad_json(message='Invalid Credentials')

        except Exception as ex:
            return bad_json(message="Internal Server: {}".format(ex))

    ret = request.GET.get('ret', '/')
    data['ret'] = ret.split('?')[0]
    return render(request, "views/login.html", data)


def error_404_view(request):
    data = {'title': 'Handler 404 - Page not found'}
    return render(request, '404.html', data)


def error_500_view(request):
    data = {'title': 'Handler 500 - Server Error'}
    return render(request, '500.html', data)


# API to check user session activity
def check_user_activity(request):
    if 'last_activity' in request.session:
        last_activity = datetime.strptime(request.session['last_activity'], '%Y-%m-%d %H:%M:%S')
    else:
        request.session['last_activity'] = last_activity = datetime.now()

    inactivity_time = (datetime.now() - last_activity).seconds

    alert_close_session_by_timeout = True if inactivity_time > TIMEOUT_TO_ALERT_USER_SESSION else False

    close_session_by_timeout = True if inactivity_time > TIMEOUT_TO_CLOSE_USER_SESSION else False

    return ok_json({
        'alert_close_session_by_timeout': alert_close_session_by_timeout,
        'close_session_by_timeout': close_session_by_timeout,
    })


# API to reset user session activity
def reset_user_activity(request):
    request.session['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return ok_json({'message': 'Your session has been updated.'})
