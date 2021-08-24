from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from app.management.utilities.constants import AUDIT_TRAIL_ACTION_CREATED
from app.management.utilities.globals import addGlobalData
from app.management.utilities.functions import bad_json, generate_token, ok_json, audit_trail, get_ip_address

from empowerb.settings import EMAIL_ACTIVE, EMAIL_HOST_USER

from ermm.models import UserProfile, Account, UserCompany


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    """
        Users
    """
    data = {'title': 'Users', 'header_title': 'My Users'}
    addGlobalData(request, data)

    # Check is user is owner
    if not data['is_owner']:
        return HttpResponseRedirect(reverse('companies'))

    # Get the Account for auth user
    my_account = Account.objects.filter(owner=data['user'])[0]

    if request.method == 'POST':

        try:
            with transaction.atomic():

                firstname = request.POST['u_firstname']
                lastname = request.POST['u_lastname']
                email = request.POST['u_email']
                phone = request.POST['u_phone']
                selected_companies_ids = request.POST['selected_companies_ids']

                if not selected_companies_ids:
                    return bad_json(message='You have to select at least one company')

                if not email:
                    return bad_json(message='Email is required')

                try:
                    validate_email(email)
                except Exception:
                    return bad_json(message='Invalid email address')

                if User.objects.filter(email=email).exists():
                    return bad_json(message='Email is already taken, please try with another email')

                new_user = User(first_name=firstname,
                                last_name=lastname,
                                email=email,
                                username=email,
                                is_active=True)    # inactive by default until user activates his account
                new_user.save()

                my_profile = UserProfile(user=new_user,
                                         phone=phone,
                                         token=generate_token())
                my_profile.save()

                # UserCompany objects (access per company Ticket 208)
                for company_id in selected_companies_ids.split(','):
                    if not UserCompany.objects.filter(user=new_user, company_id=company_id).exists():
                        user_company = UserCompany(user=new_user,
                                                   company_id=company_id)
                        user_company.save()

                if EMAIL_ACTIVE:
                    msg_html = render_to_string('emails/newuser.html', {'my_profile': my_profile})
                    send_mail("Activate Account - EmpowerRM", "", EMAIL_HOST_USER, [new_user.email], html_message=msg_html)

                # Audit Trail
                # audit_trail(username=request.user.username,
                #             action=AUDIT_TRAIL_ACTION_CREATED,
                #             ip_address=get_ip_address(request),
                #             entity1_name=my_profile.__class__.__name__,
                #             entity1_id=my_profile.get_id_str(),
                #             entity1_reference=my_profile.user.username)

                return ok_json(data={'result': 'ok', 'redirect_url': reverse('users')})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    # Users of the company
    data['my_related_users'] = User.objects.filter(usercompany__company__account=my_account).distinct().exclude(id=data['user'].id).distinct()

    # init 'is_active' class  for option in the menu
    data['menu_option_users'] = True

    return render(request, "users/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
def activation(request):
    """
        Users Activation
    """
    data = {'title': 'Users Activation'}
    addGlobalData(request, data)

    if request.method == 'POST':

        try:
            with transaction.atomic():

                token = request.POST.get('token', '')
                new_password = request.POST.get('new_user_password', '')
                confirm_password = request.POST.get('new_user_password_confirm', '')

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
                user.is_active = True  # activate user
                user.save()

                # for security reasons we can update the token for the user profile
                my_profile.token = generate_token()
                my_profile.save()

                return ok_json(data={'result': 'ok', 'redirect_url': reverse('login')})

        except Exception as ex:
            return bad_json(message=ex.__str__())

    data['token'] = request.GET.get('token', '')
    return render(request, "users/activation.html", data)
