import json
import logging
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse


logger = logging.getLogger(__name__)


class HTMXMessageMixin:
    def htmx_message(
        self,
        *,
        message_text: str,
        message_type: str = "success",
        response: Optional[HttpResponse] = None,
        reswap_none: bool = False,
    ) -> HttpResponse:
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
    message_text = "Сначала войдите в аккаунт."
    message_type = "info"

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get("Hx-Request") and not request.user.is_authenticated:
            return self.htmx_message(
                message_text=self.message_text,
                message_type=self.message_type,
                reswap_none=True,
            )

        return super().dispatch(request, *args, **kwargs)


class LoginRequiredRedirectHTMXMixin(LoginRequiredMixin):
    """
    Расширение LoginRequiredMixin, чтобы HTMX делал редирект на страницу логина.
    """

    def handle_no_permission(self):
        if self.request.headers.get("Hx-Request"):
            return HttpResponse(headers={"HX-Redirect": f"{self.get_login_url()}"})
        return super().handle_no_permission()


class HTMXHandle404Mixin:
    """
    Обрабатывает Http404 для HTMX-запросов, чтобы не выбрасывать ошибку,
    а триггерить обновление комментариев.
    """

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)  # type: ignore
        except Http404:
            if request.headers.get("Hx-Request"):
                response = HttpResponse()
                response["HX-Trigger"] = json.dumps({"commentsUpdated": {}})
                return response
            raise
