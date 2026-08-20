FROM nginx:latest

# Создается папка для хранения исходных конфигов
RUN mkdir -p /etc/nginx/source_configs

# Копирование Nginx конфигураций для http и https
COPY http.conf /etc/nginx/source_configs/http.conf
COPY https.conf /etc/nginx/source_configs/https.conf
# Копирование скрипта инициализации контейнера
COPY entrypoint.sh /entrypoint.sh

# Команда делает скрипт исполняемым,
# chmod - изменяет права доступа,
# +x - задает право на запуск файла как программы.
RUN chmod +x /entrypoint.sh

# Очистка рабочей директории конфигов,
# -r - рекурсивно удаляет подпапки и их содержимое.
RUN rm -rf /etc/nginx/conf.d/*

ENTRYPOINT ["/entrypoint.sh"]