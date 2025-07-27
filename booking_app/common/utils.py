from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.utils.functional import cached_property
from django.core.paginator import Paginator

class LazyPaginator(Paginator):
    """
    Custom paginator that delays counting the queryset until needed.
    """
    @cached_property
    def count(self):
        return super().count
    
class CustomPagination(PageNumberPagination):
    """
    Custom pagination class with lazy initialization for conversations.
    Limits API responses to 20 items per page.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginator(self, queryset):
        """Return a LazyPaginator instance to defer counting."""
        return LazyPaginator(queryset, self.page_size)
    def paginate_queryset(self, queryset, request, view=None):
        """
        Lazily paginate the queryset, deferring evaluation until needed.
        """
        self.request = request
        self.paginator = self.get_paginator(queryset)
        page_number = self.get_page_number(request, self.paginator)
        if page_number is None:
            return None
        try:
            self.page = self.paginator.page(page_number)
        except Exception as e:
            raise ValueError(f"Invalid page: {e}")
        return list(self.page.object_list)

    def get_paginated_response(self, data):
        """Return response with lazy-evaluated pagination metadata."""
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.paginator.count,  # Triggers count only when needed
            'results': data
        })