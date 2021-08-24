from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from app.management.utilities.globals import addGlobalData
from ermm.models import Company


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        User's companies
    """
    data = {'title': 'Companies', 'header_title': 'My Companies'}
    addGlobalData(request, data)

    # EA-1012 - If user is assigned to only one company, take them right to the dashboard
    if len(data['user_companies']) == 1:
        # EA-1576 Add a company setting to set the start page
        company = Company.objects.get(id=data['user_companies'][0].id)
        company_settings = company.my_company_settings()
        data['cb_start_page'] = company_settings.cb_start_page
        response = redirect(f"/{data['user_companies'][0].database}{company_settings.cb_start_page}")
        # response = redirect(f"/{data['user_companies'][0].database}/dashboard?range=MTD")
        return response

    return render(request, "views/companies.html", data)
