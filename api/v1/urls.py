from django.conf.urls import include
from django.urls import path

from rest_framework.routers import DefaultRouter

from api.v1.quickbooks.viewsets import QuickbooksConfigurationsViewSet, QuickbooksTransactionsViewSet

# Router obj
router = DefaultRouter(trailing_slash=False)

# Quickbooks Chargebacks API
router.register(r'QB/configurations', QuickbooksConfigurationsViewSet, basename='QB_configurations')
router.register(r'QB/transactions', QuickbooksTransactionsViewSet, basename='QB_transactions')


urlpatterns = [
    path(r'', include(router.urls)),
]
