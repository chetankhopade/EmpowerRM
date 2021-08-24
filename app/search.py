from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from app.management.utilities.globals import addGlobalData

from erms.models import Contract, Item, DirectCustomer, IndirectCustomer


@login_required(redirect_field_name='ret', login_url='/login')
def views(request):
    """
        Search controller
    """
    data = {'title': 'Search Results', 'header_title': 'Search Results'}
    addGlobalData(request, data)

    if not data['company'] or not data['has_access_to_company']:
        return HttpResponseRedirect(reverse('companies'))

    search = request.GET.get('s', '')
    if search:

        # Contracts
        data['contracts'] = Contract.objects.filter(number__icontains=search)[:20]

        # Items
        data['items'] = Item.objects.filter(
            Q(ndc__icontains=search) | Q(description__icontains=search) | Q(account_number__icontains=search)
        ).distinct()[:20]

        # DirectCustomers
        data['direct_customers'] = DirectCustomer.objects.filter(
            Q(name__icontains=search) | Q(account_number__icontains=search)
        ).distinct()[:20]

        # IndirectCustomers
        data['indirect_customers'] = IndirectCustomer.objects.filter(
            Q(company_name__icontains=search) | Q(location_number__icontains=search)
        ).distinct()[:20]

        return render(request, "search/search.html", data)
