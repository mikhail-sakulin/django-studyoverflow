"""HTMX-миксины."""

import json
import logging
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse


logger = logging.getLogger(__name__)


class HTMXMessageMixin:
    """
    Миксин для формирования сообщения клиенту при HTMX запросе.
    """

    def htmx_message(
        self,
        *,
        message_text: str,
        message_type: str = "success",
        response: Optional[HttpResponse] = None,
        reswap_none: bool = False,
    ) -> HttpResponse:
        """
        Формирует сообщение и добавляет HTMX-событие showMessage в ответ.
        """
        response = response or HttpResponse()

        if reswap_none:
            response["HX-Reswap"] = "none"

        # текущий header
        hx_trigger = response.get("HX-Trigger")

        # десериализация, если есть данные, иначе пустой словарь
        if hx_trigger:
            try:
                hx_data = json.loads(hx_trigger)
            except json.JSONDecodeError:
                logger.warning(
                    "Ошибка декодирования HX-Trigger.",
                    extra={"raw_header": hx_trigger, "event_type": "hx_trigger_decode_error"},
                )
                hx_data = {}
        else:
            hx_data = {}

        # новое событие showMessage
        hx_data["showMessage"] = {
            "text": message_text,
            "type": message_type,
        }

        # сохранение обратно в response
        response["HX-Trigger"] = json.dumps(hx_data)

        return response


class LoginRequiredHTMXMixin(LoginRequiredMixin, HTMXMessageMixin):
    """
    Миксин для обработки HTMX-запросов неаутентифицированных пользователей.
    """

    message_text: str = "Сначала войдите в аккаунт."
    message_type: str = "info"

    def dispatch(self, request, *args, **kwargs):
        """
        Перехватывает HTMX-запросы неавторизованных пользователей.
        Вместо редиректа возвращает сообщение.
        """
        if request.headers.get("Hx-Request") and not request.user.is_authenticated:
            return self.htmx_message(
                message_text=self.message_text,
                message_type=self.message_type,
                reswap_none=True,
            )

        return super().dispatch(request, *args, **kwargs)


class LoginRequiredRedirectHTMXMixin(LoginRequiredMixin):
    """
    Миксин для выполнения редиректа на страницу логина
    при HTMX-запросе неавторизованного пользователя.
    """

    def handle_no_permission(self):
        if self.request.headers.get("Hx-Request"):
            return HttpResponse(headers={"HX-Redirect": f"{self.get_login_url()}"})
        return super().handle_no_permission()


class HTMXHandle404CommentMixin:
    """
    Миксин для обработки Http404 в HTMX-запросах комментариев.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Перехватывает Http404 и возвращает HTMX-событие обновления комментариев.

        Используется для ситуаций, когда комментарий был удалён и необходимо обновить список.
        """
        try:
            return super().dispatch(request, *args, **kwargs)  # type: ignore
        except Http404:
            if request.headers.get("Hx-Request"):
                response = HttpResponse()
                response["HX-Trigger"] = json.dumps({"commentsUpdated": {}})
                return response
            raise
