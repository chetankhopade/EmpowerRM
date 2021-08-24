from rest_framework import permissions

from ermm.models import Company, QuickbooksConfigurations


class IsValidToken(permissions.BasePermission):
    """
    Custom permission to validate token
    """
    def has_permission(self, request, view):
        try:
            return QuickbooksConfigurations.objects.filter(token=request.META['HTTP_TOKEN']).exists()
        except Exception as ex:
            print(ex.__str__())
            return False


class IsAuthorized(permissions.BasePermission):
    """
    Custom permission to validate token to have access to endpoints
    """
    def has_permission(self, request, view):
        # validate token vs company
        try:
            company = Company.objects.get(id=request.data['company_id'])
            token = request.META['HTTP_TOKEN']
            return QuickbooksConfigurations.objects.filter(company=company, token=token).exists()
        except Exception as ex:
            print(ex.__str__())
            return False
