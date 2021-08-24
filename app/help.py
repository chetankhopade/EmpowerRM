from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from app.management.utilities.globals import addGlobalData


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        Help Center
    """
    data = {'title': 'Help Center', 'header_title': 'Help Center'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    # init 'is_active' class  for option in the menu
    data['menu_option_help_center'] = True

    return render(request, "help_center/help_center.html", data)
