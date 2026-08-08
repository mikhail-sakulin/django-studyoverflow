# Официальный образ от Microsoft с установленными браузерами
FROM mcr.microsoft.com/playwright/python:v1.61.0-jammy

WORKDIR /e2e

COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY . .

# --tracing=retain-on-failure - интерактивный лог тестов, если тесты прошли - удаляется,
# если тесты не прошли, лог сохраняется;
# --output=./test-results - папка внутри контейнера, куда pytest будет сохранять файлы, сгенерированные во время ошибок
#
# В качестве логов создается архив для каждого упавшего теста, посмотреть логи можно, загрузив архив
# на сайт https://trace.playwright.dev/
CMD ["pytest", "--tracing=retain-on-failure", "--output=./test-results", "-v", "-n", "4"]
