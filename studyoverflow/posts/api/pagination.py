from rest_framework.response import Response

from navigation.api.pagination import CustomPageNumberPagination


class PostCommentsPagination(CustomPageNumberPagination):
    """
    Кастомная пагинация списка комментариев поста.

    Помимо стандартной информации о пагинации возвращает общее количество
    комментариев у поста, учитывая дочерние комментарии (ответы).
    """

    def get_paginated_response(self, data):
        post = self.request.parser_context["view"].get_post()

        return Response(
            {
                "parents_comments_count": self.page.paginator.count,
                "all_comments_count": post.comments_count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )
