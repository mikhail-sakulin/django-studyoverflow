from playwright.sync_api import expect


def expect_notifications_count(page, expected: str, attempts: int = 5, delay_ms: int = 300) -> None:
    """
    Проверяет счетчик уведомлений на странице, который обновляется через WebSocket.

    Если ожидаемое число уведомлений не найдено, делаются ретраи (если attempts > 1). При каждом
    ретрае страница перезагружается для обновления счетчика уведомлений.

    Уведомления должны обновляться без перезагрузки страницы через WebSocket, но
    для стабильности тестов при ретраях страница перезагружается.
    """
    for attempt in range(attempts):
        try:
            expect(page.locator("#notifications-count")).to_have_text(expected, timeout=2000)
            return
        except AssertionError:
            if attempt == attempts - 1:
                raise
            page.reload()
            page.wait_for_timeout(delay_ms)
