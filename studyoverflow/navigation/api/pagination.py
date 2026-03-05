from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Кастомная пагинация для api запросов.
    """

    page_size = 7
    page_size_query_param = "page_size"
    max_page_size = 100
