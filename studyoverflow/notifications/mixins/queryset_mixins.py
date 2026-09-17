from django.contrib.contenttypes.prefetch import GenericPrefetch

from posts.models import Comment, Like, Post


class NotificationOptimizeMixin:
    """
    Миксин для оптимизации QuerySet уведомлений.

    "GenericPrefetch" используется, поскольку из-за универсальности уведомлений поле
    "content_object" ("GenericForeignKey("content_type", "object_id")") ссылается на связанный
    объект через пару полей "content_type" и "object_id". "GenericPrefetch" работает по аналогии
    с "Prefetch", только он группирует связанные объекты по их типам и предзагружает их отдельными
    SQL-запросами. При обычном "Prefetch" для одной связи выполняется один дополнительный
    SQL-запрос, а при "GenericPrefetch" число дополнительных SQL-запросов пропорционально числу
    уникальных типов связанных объектов (и их вложенным связям).

    Это позволяет предотвратить проблему "N+1" при использовании "GenericForeignKey" связи.
    """

    def optimize_notification_queryset(self, queryset):
        queryset = (
            queryset.select_related("actor", "content_type")
            .only(
                "user_id",
                "notification_type",
                "message",
                "is_read",
                "time_create",
                "actor_id",
                "actor__id",
                "actor__username",
                "actor__avatar",
                "actor__avatar_small_size1",
                "actor__avatar_small_size2",
                "actor__avatar_small_size3",
                "actor__role",
                "content_type_id",
                "content_type__model",
                "object_id",
            )
            .prefetch_related(
                GenericPrefetch(
                    "content_object",
                    [
                        Post.objects.only("id", "slug"),
                        Comment.objects.select_related("post").only("id", "post__id", "post__slug"),
                        Like.objects.prefetch_related(
                            GenericPrefetch(
                                "content_object",
                                [
                                    Post.objects.only("id", "slug"),
                                    Comment.objects.select_related("post").only(
                                        "id", "post__id", "post__slug"
                                    ),
                                ],
                            )
                        ),
                    ],
                )
            )
        )

        return queryset
