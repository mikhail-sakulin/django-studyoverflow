#!/bin/sh
# Если какая-либо команда завершится ошибкой, скрипт сразу остановится
set -e

# Очистка conf.d (старых конфигурационных файлов) в случае перезапуска контейнера,
# -f - чтобы скрипт не падал, если папка пуста.
rm -f /etc/nginx/conf.d/*.conf

# NGINX_SSL_ENABLED - переменная окружения, задается в docker-compose или в .env.prod файле
if [ "$NGINX_SSL_ENABLED" = "True" ] || [ "$NGINX_SSL_ENABLED" = "true" ]; then
    # echo - выводит текст в stdout
    echo "Using HTTPS configuration"
    # cp - копирует файл
    cp /etc/nginx/source_configs/https.conf /etc/nginx/conf.d/default.conf
else
    echo "Using HTTP configuration"
    cp /etc/nginx/source_configs/http.conf /etc/nginx/conf.d/default.conf
fi

# Запуск nginx в foreground (на переднем плане, не в фоновом режиме).
# Если скрипт запускает программу, создается дочерний процесс, а скрипт висит в памяти и ждет
# завершения дочернего процесса.
# exec - завершает процесс скрипта и вместо него запускает программу с тем же самым ID процесса,
# Nginx сможет получать команды от docker.
# -g "daemon off;" - запрещает Nginx уходить в фоновый режим, иначе Docker сочтет, что работа окончена
# и остановит контейнер.
exec nginx -g "daemon off;"