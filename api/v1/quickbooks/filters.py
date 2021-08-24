from rest_framework import filters


class QuickbooksConfigurationsFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        try:
            return queryset.filter(token=request.META['HTTP_TOKEN'])
        except Exception as ex:
            print(ex.__str__())
            return []
