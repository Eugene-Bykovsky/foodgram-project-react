from rest_framework.pagination import PageNumberPagination


class CustomRecipesPagination(PageNumberPagination):
    page_size = 6


class CustomUsersPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6
