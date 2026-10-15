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

    def get_paginated_response_schema(self, schema):
        """
        Метод перехватывается drf-spectacular для генерации
        OpenAPI-схемы пагинации списка комментариев поста.
        """
        return {
            "type": "object",
            "required": ["parents_comments_count", "all_comments_count", "results"],
            "properties": {
                "parents_comments_count": {
                    "type": "integer",
                    "example": 12,
                    "description": "Общее количество родительских комментариев.",
                },
                "all_comments_count": {
                    "type": "integer",
                    "example": 34,
                    "description": "Общее количество всех комментариев (включая дочерние).",
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://127.0.0.1/api/v1/posts/1/comments/?page=3",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://127.0.0.1/api/v1/posts/1/comments/?page=1",
                },
                "results": schema,
            },
        }
