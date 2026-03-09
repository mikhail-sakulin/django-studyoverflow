from django.contrib.contenttypes.prefetch import GenericPrefetch
from posts.models import Comment, Like, Post


class NotificationOptimizeMixin:
    """
    Миксин для оптимизации QuerySet уведомлений.
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
                "actor__username",
                "actor__avatar",
                "actor__avatar_small_size1",
                "actor__avatar_small_size2",
                "actor__avatar_small_size3",
                "actor__role",
                "content_type_id",
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
