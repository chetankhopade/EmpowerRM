from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app.management.utilities.functions import bad_json, ok_json, model_to_dict_safe
from app.management.utilities.globals import addGlobalData
from erms.models import Recipient


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def list(request):
    data = {'title': 'Recipients'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            if request.POST['rt'] == 'p':
                recipients = Recipient.objects.filter(is_processing=True)
            else:
                recipients = Recipient.objects.filter(is_processing=False)
            return ok_json(data={'recipients': [model_to_dict_safe(x) for x in recipients]})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def add(request):
    """
        Add Recipient
    """
    data = {'title': 'Add Recipient'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            email = request.POST.get('email', '')
            first_name = request.POST.get('firstname', '')
            last_name = request.POST.get('lastname', '')
            is_processing = True if request.POST.get('rtype', 'p') == 'p' else False

            if not first_name:
                return bad_json(message='First Name is required ')

            if not email:
                return bad_json(message='Email is required')

            recipient, _ = Recipient.objects.get_or_create(email=email, is_processing=is_processing)
            recipient.first_name = first_name
            recipient.last_name = last_name
            recipient.save()
            return ok_json(data={'message': 'Recipient added successfully!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
@csrf_exempt
def remove(request, recipient_id):
    """
        Remove Recipient
    """
    data = {'title': 'Remove Recipient'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    try:
        with transaction.atomic():
            recipient = Recipient.objects.get(id=recipient_id)
            recipient.delete()
            return ok_json(data={'message': 'Successfully removed recipient!'})

    except Exception as ex:
        return bad_json(message=ex.__str__())
