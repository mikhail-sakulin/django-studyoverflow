import logging

from django.http import HttpRequest

from .online import get_cached_online_user_ids


logger = logging.getLogger(__name__)


class UserOnlineFilterMixin:
    """
    Миксин для фильтрации queryset пользователей по признаку "онлайн".

    Использует GET-параметр "online" для определения типа фильтрации.
    """

    request: HttpRequest

    online_param = "online"

    def filter_by_online(self, queryset):
        """
        Применяет фильтрацию пользователей по статусу онлайн.
        """
        online = self.request.GET.get(self.online_param, "any")

        if online == "any":
            return queryset

        self.online_ids = get_cached_online_user_ids()

        if online == "online":
            return queryset.filter(id__in=self.online_ids)

        return queryset.exclude(id__in=self.online_ids)

    def get_online_ids(self):
        """Возвращает список ID пользователей, находящихся онлайн."""
        return getattr(self, "online_ids", get_cached_online_user_ids())


class UserSortMixin:
    """
    Миксин для сортировки queryset пользователей.
    """

    request: HttpRequest

    sort_param = "user_sort"
    order_param = "user_order"

    sort_map = {
        "name": "username",
        "reputation": "reputation",
        "posts": "posts_count",
        "comments": "comments_count",
    }

    default_sort = "reputation"
    default_order = "desc"

    def apply_sorting(self, queryset):
        """
        Сортирует queryset пользователей.

        Если параметры сортировки некорректны, используются значения по умолчанию.
        Всегда добавляется вторичная сортировка по username.
        """

        sort = self.request.GET.get(self.sort_param, self.default_sort)
        order = self.request.GET.get(self.order_param, self.default_order)

        sort = sort if sort in self.sort_map else self.default_sort
        order = order if order in ("asc", "desc") else self.default_order

        field = self.sort_map[sort]
        if order == "desc":
            field = f"-{field}"

        return queryset.order_by(field, "username")


class UserHTMXPaginationMixin:
    """
    Миксин для постраничной загрузки пользователей через HTMX.

    Использует offset-limit пагинацию.

    GET-параметры:
    - offset — смещение выборки
    - limit  — количество объектов на страницу
    """

    request: HttpRequest

    paginate_htmx_by = 9
    offset_param = "offset"
    limit_param = "limit"

    def paginate_queryset(self, queryset):
        """
        Применяет offset-limit пагинацию к queryset.

        Атрибуты:
        - self.offset    — текущий offset
        - self.limit     — текущий limit
        - self.remaining — флаг наличия следующей страницы
        """

        offset = self.request.GET.get(self.offset_param, 0)
        limit = self.request.GET.get(self.limit_param, self.paginate_htmx_by)

        try:
            offset = int(offset)
            limit = int(limit)
        except ValueError:
            logger.warning(
                "Некорректные параметры пагинации.",
                extra={
                    "offset_param": self.offset_param,
                    "limit_param": self.limit_param,
                    "offset_value": self.request.GET.get(self.offset_param),
                    "limit_value": self.request.GET.get(self.limit_param),
                    "event_type": "htmx_pagination_invalid_params",
                },
            )
            return queryset.none()

        self.offset = offset
        self.limit = limit

        if limit > 0:
            self.remaining = queryset[offset + limit : offset + limit + 1].exists()
            return queryset[offset : offset + limit]

        self.remaining = False
        return queryset[offset:]
