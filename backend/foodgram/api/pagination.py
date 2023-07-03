from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size = 5
