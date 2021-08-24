import time

import requests

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from rest_framework import status

from app.management.utilities.functions import ok_json, bad_json
from app.management.utilities.globals import addGlobalData
from empowerb.settings import (ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_SCOPE, ZOHO_AUTH_BASE_URI, ZOHO_MDH_ORG_ID)


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    data = {'title': 'Administration - Help Desk', 'header_title': 'Administration > Help Desk'}
    addGlobalData(request, data)

    # get code from uri callback from zoho
    code = request.GET.get('code', '')

    # callback redirect uri (required by zoho)
    zoho_redirect_uri = reverse('administration_help_desk')

    if code:

        payload = {
            "code": code,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "scope": ZOHO_SCOPE,
            "redirect_uri": zoho_redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(f"{ZOHO_AUTH_BASE_URI}/token", data=payload)
        response_obj = response.json()

        if 'error' in response_obj.keys():
            data['error'] = response_obj['error']
        else:
            data['access_token'] = response_obj['access_token']
            # data['refresh_token'] = response_obj.get('refresh_token')

    data['zoho_authorization_grant_uri'] = f"{ZOHO_AUTH_BASE_URI}/auth?response_type=code&client_id={ZOHO_CLIENT_ID}&scope={ZOHO_SCOPE}&redirect_uri={zoho_redirect_uri}&access_type=offline"
    data['zoho_mdh_org_id'] = ZOHO_MDH_ORG_ID

    data['menu_option'] = 'menu_administration_helpdesk'
    return render(request, "administration/helpdesk/view.html", data)


@login_required(redirect_field_name='ret', login_url='/login')
def tickets(request):
    try:
        access_token = request.POST['access_token']
        org_id = request.POST['org_id']
        if access_token != 'None' and org_id != 'None':
            response = requests.get(
                "https://desk.zoho.com/api/v1/tickets",
                headers={
                    'Authorization': f'Zoho-oauthtoken {access_token}',
                    'orgId': org_id
                }
            )
            if response.status_code == status.HTTP_200_OK:
                return ok_json(data={'tickets': response.json()['data']})
            return bad_json(message=f'{response.status_code}')

        return bad_json(message='Access Token is missing. Grant Access again to auth.')
    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def add_comment_to_ticket(request, ticket_id):
    try:
        access_token = request.POST['access_token']
        org_id = request.POST['org_id']
        comments = request.POST['comments']
        if access_token != 'None' and org_id != 'None' and comments:

            response = requests.post(
                f"https://desk.zoho.com/api/v1/tickets/{ticket_id}/comments",
                headers={
                    'Authorization': f'Zoho-oauthtoken {access_token}',
                    'orgId': org_id
                },
                json={
                    "content": comments
                }
            )

            time.sleep(1)
            if response.status_code == status.HTTP_200_OK:
                return ok_json(data={'message': 'Comment has been succesfully sent to Zoho!'})

            return bad_json(message=f'Error getting tickets. Status Code: {response.status_code}')

    except Exception as ex:
        return bad_json(message=ex.__str__())


@login_required(redirect_field_name='ret', login_url='/login')
def close_ticket(request, ticket_id):
    try:
        access_token = request.POST['access_token']
        org_id = request.POST['org_id']
        if access_token != 'None' and org_id != 'None':

            response = requests.patch(
                f"https://desk.zoho.com/api/v1/tickets/{ticket_id}",
                headers={
                    'Authorization': f'Zoho-oauthtoken {access_token}',
                    'orgId': org_id
                },
                json={
                    "status": "Closed"
                }
            )

            time.sleep(1)
            if response.status_code == status.HTTP_200_OK:
                return ok_json(data={'message': 'Ticket has been succesfully Closed!'})

            return bad_json(message=f'Error getting tickets. Status Code: {response.status_code}')

    except Exception as ex:
        return bad_json(message=ex.__str__())
