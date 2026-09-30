# StudyOverflow
**StudyOverflow** — это веб-приложение на классическом Django-фреймворке с дополнительной реализацией REST API через Django REST Framework (DRF), созданное как платформа для вопросов и ответов по программированию по аналогии со Stack Overflow.

<img width="1705" height="1140" alt="main-page" src="https://github.com/user-attachments/assets/1a890b49-b334-410e-a947-e19c1eb8c17b" /><br>

[Содержание](#содержание) · [Структура проекта](#1-структура-проекта) · [Быстрый запуск](#23-быстрый-пробный-запуск-без-предварительной-настройки) · [ER-диаграмма](#41-er-диаграмма-кастомных-django-моделей)

## Технологии и инфраструктура
| Категория | Используемые технологии |
| :--- | :--- |
| **Backend** | ![Python](https://img.shields.io/badge/Python_3.12-%233670A0.svg?style=flat&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/Django-%23092E20.svg?style=flat&logo=django&logoColor=white) ![DRF](https://img.shields.io/badge/Django%20REST-ff1709?style=flat&logo=django&logoColor=white) ![drf-spectacular](https://img.shields.io/badge/OpenAPI_3.0-drf--spectacular-%231B9C85.svg?style=flat&logo=openapiinitiative&logoColor=white) ![Celery](https://img.shields.io/badge/Celery-%2337814A.svg?style=flat&logo=celery&logoColor=white) ![Django Channels](https://img.shields.io/badge/Django%20Channels-%23092E20.svg?style=flat&logo=django&logoColor=white) ![Daphne](https://img.shields.io/badge/ASGI-Daphne-092E20.svg?style=flat&logo=python&logoColor=white) |
| **Frontend** | ![Bootstrap](https://img.shields.io/badge/Bootstrap-%238511FA.svg?style=flat&logo=bootstrap&logoColor=white) ![HTML5](https://img.shields.io/badge/HTML5-%23E34F26.svg?style=flat&logo=html5&logoColor=white) ![CSS](https://img.shields.io/badge/CSS-%23663399.svg?style=flat&logo=css&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-%23323330.svg?style=flat&logo=javascript&logoColor=%23F7DF1E) ![htmx](https://img.shields.io/badge/htmx-%233366CC.svg?style=flat&logo=htmx&logoColor=white) ![Markdown](https://img.shields.io/badge/Markdown-%23000000.svg?style=flat&logo=markdown&logoColor=white) ![LaTeX](https://img.shields.io/badge/Latex-%23008080.svg?style=flat&logo=latex&logoColor=white) |
| **DB & Storage** | ![Postgres](https://img.shields.io/badge/Postgres-%23316192.svg?style=flat&logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white) ![S3](https://img.shields.io/badge/S3-Boto3-569A31?style=flat&logo=amazons3&logoColor=white) ![Adminer](https://img.shields.io/badge/DB_Management-Adminer-336791?style=flat&logo=postgresql&logoColor=white) |
| **Authentication** | ![Django Sessions](https://img.shields.io/badge/Session-Django-092E20?style=flat&logo=django&logoColor=white) ![DRF TokenAuth](https://img.shields.io/badge/Token-DRF-ff1709?style=flat&logo=django&logoColor=white) ![JWT](https://img.shields.io/badge/JWT-Simple_JWT-000000?style=flat&logo=jsonwebtokens&logoColor=white) ![django-allauth](https://img.shields.io/badge/OAuth-django--allauth-092E20?style=flat&logo=django&logoColor=white) ![dj-rest-auth](https://img.shields.io/badge/API_OAuth-dj--rest--auth-ff1709?style=flat&logo=django&logoColor=white) |
| **DevOps** | ![Docker](https://img.shields.io/badge/Docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white) ![Docker](https://img.shields.io/badge/Docker--compose-%230db7ed.svg?style=flat&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/Nginx-%23009639.svg?style=flat&logo=nginx&logoColor=white) ![Let's Encrypt](https://img.shields.io/badge/Let%27s_Encrypt-SSL-003A70?style=flat&logo=letsencrypt&logoColor=white) ![Certbot](https://img.shields.io/badge/Certbot-003A70?style=flat&logo=letsencrypt&logoColor=white) |
| **Monitoring** | ![Grafana Promtail](https://img.shields.io/badge/Grafana-Promtail-F46800?style=flat&logo=grafana&logoColor=white) ![Grafana Loki](https://img.shields.io/badge/Grafana-Loki-F46800?style=flat&logo=grafana&logoColor=white) ![Grafana](https://img.shields.io/badge/Grafana-%23F46800.svg?style=flat&logo=grafana&logoColor=white) ![Flower](https://img.shields.io/badge/Celery_Monitoring-Flower-e05d44?style=flat&logo=celery&logoColor=white) |
| **Code Quality** | ![Pytest](https://img.shields.io/badge/Pytest-%23ffffff.svg?style=flat&logo=pytest&logoColor=2f9fe3) ![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=flat&logo=Playwright&logoColor=white) ![black](https://img.shields.io/badge/black-000000?style=flat&logo=python&logoColor=white) ![isort](https://img.shields.io/badge/isort-1674b1?style=flat&logo=python&logoColor=white) ![flake8](https://img.shields.io/badge/flake8-3776AB?style=flat&logo=python&logoColor=white) ![mypy](https://img.shields.io/badge/mypy-2b5b84?style=flat&logo=python&logoColor=white) |

## Содержание
- [1. Структура проекта](#1-структура-проекта)
- [2. Описание, настройка и запуск сборок проекта](#2-описание-настройка-и-запуск-сборок-проекта)
  - [2.1 Системные требования для запуска](#21-системные-требования-для-запуска)
  - [2.2 Копирование файлов для запуска](#22-копирование-файлов-для-запуска)
  - [2.3 Быстрый пробный запуск без предварительной настройки](#23-быстрый-пробный-запуск-без-предварительной-настройки)
  - [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения)
  - [2.5 Особенности и настройка dev-сборки](#25-особенности-и-настройка-dev-сборки)
  - [2.6 Запуск dev-сборки](#26-запуск-dev-сборки)
  - [2.7 Особенности и настройка prod- и prod-lite-сборок](#27-особенности-и-настройка-prod--и-prod-lite-сборок)
  - [2.8 Запуск prod- и prod-lite-сборок](#28-запуск-prod--и-prod-lite-сборок)
- [3. Настройка HTTP/HTTPS в Nginx, использование Certbot](#3-настройка-httphttps-в-nginx-использование-certbot)
  - [3.1 Логика выбора HTTP- и HTTPS-конфигураций Nginx](#31-логика-выбора-http--и-https-конфигураций-nginx)
  - [3.2 Использование Certbot для получения и продления SSL-сертификатов](#32-использование-certbot-для-получения-и-продления-ssl-сертификатов)
- [4. Особенности Django-проекта](#4-особенности-django-проекта)
  - [4.1 ER-диаграмма кастомных Django-моделей](#41-er-диаграмма-кастомных-django-моделей)
  - [4.2 Кастомные Django-приложения](#42-кастомные-django-приложения)
  - [4.3 Система уведомлений](#43-система-уведомлений)
  - [4.4 Роли пользователей, права и группы](#44-роли-пользователей-права-и-группы)
  - [4.5 Способы аутентификации, бекенды и классы аутентификации](#45-способы-аутентификации-бекенды-и-классы-аутентификации)
    - [4.5.1 Web](#451-web)
    - [4.5.2 Api](#452-api)
  - [4.6 Аватары пользователей: генерация, хранение и использование](#46-аватары-пользователей-генерация-хранение-и-использование)
  - [4.7 GIN-индексы с расширением pg_trgm для постов](#47-gin-индексы-с-расширением-pg_trgm-для-постов)
  - [4.8 Поддержка Markdown и LaTeX](#48-поддержка-markdown-и-latex)
  - [4.9 Кеширование](#49-кеширование)
  - [4.10 Онлайн-статус пользователей через Redis](#410-онлайн-статус-пользователей-через-redis)
- [5. CI/CD-пайплайны](#5-cicd-пайплайны)
  - [5.1 Используемые CI/CD-пайплайны](#51-используемые-cicd-пайплайны)
  - [5.2 CI: проверка кода Django-проекта](#52-ci-проверка-кода-django-проекта)
  - [5.3 CD Checks: проверка prod- и prod-lite-сборок](#53-cd-checks-проверка-prod--и-prod-lite-сборок)
  - [5.4 CD Publish and Deploy: публикация образов и деплой](#54-cd-publish-and-deploy-публикация-образов-и-деплой)
  - [5.5 CD Tag Release: релиз по git-тегу](#55-cd-tag-release-релиз-по-git-тегу)
  - [5.6 GitHub переменные и секреты для CI/CD-пайплайнов](#56-github-переменные-и-секреты-для-cicd-пайплайнов)
- [6. Тестирование](#6-тестирование)
  - [6.1 Модульные и интеграционные тесты через pytest](#61-модульные-и-интеграционные-тесты-через-pytest)
  - [6.2 Сценарии запусков модульных и интеграционных тестов](#62-сценарии-запусков-модульных-и-интеграционных-тестов)
  - [6.3 E2E-тесты через Playwright](#63-e2e-тесты-через-playwright)
  - [6.4 Запуск E2E-тестов](#64-запуск-e2e-тестов)
- [7. Инструменты разработки](#7-инструменты-разработки)
  - [7.1 Pre-commit](#71-pre-commit)
  - [7.2 Сборка и фиксация зависимостей через pip-tools](#72-сборка-и-фиксация-зависимостей-через-pip-tools)
  - [7.3 Docker-образы](#73-docker-образы)
  - [7.4 Профилирование через pyinstrument](#74-профилирование-через-pyinstrument)
  - [7.5 Создание и применение фикстур — JSON-файлов с данными](#75-создание-и-применение-фикстур--json-файлов-с-данными)

## 1. Структура проекта

```plaintext
.github/workflows/              # CI/CD пайплайны GitHub Actions

e2e/                            # End-to-End тесты через Playwright (на Python) и их Docker-конфигурация
├── tests/                      # Сценарии E2E-тестов
└── ...

monitoring/                     # Стек для логирования запущенного проекта
├── grafana/                    # Веб-платформа для просмотра и поиска логов
├── loki/                       # Специализированная БД для хранения логов для Grafana
└── promtail/                   # Агент для сбора и отправки логов в Loki

nginx/                          # Конфигурации Nginx (Reverse Proxy, HTTP/HTTPS)

studyoverflow/                  # Корневой каталог Django-проекта
│
├── navigation/                 # Django-приложение с общими компонентами
│   ├── api/                    # OpenAPI-схемы аутентификации (swagger_extensions)
│   ├── templates/              # HTML-шаблоны для header, footer, главной страницы и Django-messages
│   ├── tests/                  # Некоторые интеграционные тесты Django-проекта
│   ├── menu.py                 # Конфигурация пунктов меню для header и footer
│   ├── middleware.py           # Логирование запросов и определение источника запроса (web/api)
│   ├── signals.py              # Синхронизация Site с переменной окружения SITE_DOMAIN при миграциях
│   ├── sitemaps.py             # Sitemap главной страницы, страниц списков постов и пользователей
│   ├── views.py                # Web-views для главной страницы, healthcheck и кастомные обработчики 400-ых и 500-ых ошибок
│   └── ...
├── notifications/              # Django-приложение системы уведомлений пользователей
│   ├── api/                    # REST API (DRF) views и serializers уведомлений
│   ├── mixins/                 # Общие миксины api-views и web-views
│   ├── services/               # Сервисный слой обработчиков создания уведомлений
│   ├── tests/                  # Юнит и интеграционные тесты приложения
│   ├── consumers.py            # WebSocket-консьюмеры (Django Channels)
│   ├── models.py               # Универсальная модель уведомления
│   ├── signals.py              # Обработчики Django-сигналов для системы уведомлений
│   ├── tasks.py                # Celery-задачи создания уведомлений и отправки WebSocket-событий в Django Channels
│   ├── views.py                # Web-views системы уведомлений, включая обработчики htmx-запросов
│   └── ...
├── posts/                      # Django-приложение постов, тегов, комментариев и лайков
│   ├── api/                    # REST API (DRF) views, serializers и permissions приложения
│   ├── mixins/                 # Общие миксины api-views и web-views
│   ├── services/               # Сервисный слой: кеш, валидаторы, обработка текста, включая markdown и bleach
│   ├── tests/                  # Юнит и интеграционные тесты приложения
│   ├── views/                  # Web-views приложения, включая обработчики htmx-запросов
│   │   ├── comment_views.py    # Представления для CRUD-операций с комментариями
│   │   ├── like_views.py       # Представления для создания и удаления лайков
│   │   └── post_views.py       # Представления для CRUD-операций с постами
│   ├── models.py               # Модели тега, поста, комментария и лайка
│   ├── signals.py              # Обработчики Django-сигналов: поля-счетчики для постов и комментариев, инвалидация кеша
│   ├── tasks.py                # Celery-задачи синхронизации денормализованных полей-счетчиков с данными из БД
│   └── ...
├── users/                      # Django-приложение системы пользователей и аутентификации
│   ├── api/                    # REST API (DRF) views, serializers, authentication и permissions приложения
│   ├── management/             # Кастомная django manage.py-команда (create_superuser_from_env)
│   ├── mixins/                 # Общие миксины api-views и web-views
│   ├── services/               # Сервисный слой: модерация, обработка аватарок, кеш, онлайн-статус и другое
│   ├── tests/                  # Юнит и интеграционные тесты приложения
│   ├── middleware.py           # Отслеживание активности и logout для заблокированных пользователей
│   ├── models.py               # Модель пользователя
│   ├── signals.py              # Обработчики Django-сигналов: логирование, инвалидация кеша и другое
│   ├── tasks.py                # Celery-задачи асинхронной обработки изображений (аватарок) и другое
│   ├── views.py                # Web-views для аутентификации и CRUD-операций с аккаунтами пользователей
│   └── ...
├── studyoverflow/              # Пакет конфигурации Django проекта
│   │
│   ├── settings/               # Пакет настроек проекта
│   │   ├── __init__.py         # Точка импорта настроек (кроме тестирования)
│   │   ├── auth.py             # Аутентификация: кастомная модель User, OAuth, JWT (simplejwt + dj_rest_auth), валидаторы паролей
│   │   ├── base.py                         # Базовые настройки: .env, безопасность, INSTALLED_APPS, MIDDLEWARE, TEMPLATES, ASGI/WSGI, email, локализация, HTTPS
│   │   ├── celery_channel_cache.py         # Конфигурации Celery, Django Channels (Redis), celery-once и кеш через django-redis
│   │   ├── database_s3storage_static.py    # Подключение БД, S3-хранилища и статики
│   │   ├── drf.py                          # Настройки Django REST Framework (DRF) и OpenAPI (drf-spectacular)
│   │   ├── logging.py          # Конфигурация логирования
│   │   └── test.py             # Точка импорта настроек при тестировании, переопределение настроек при тестировании
│   ├── __init__.py
│   ├── asgi.py                 # Точка входа ASGI, используется из-за наличия WebSockets через Django Channels
│   ├── celery.py               # Инициализация и конфигурация Celery
│   ├── urls.py                 # Главный файл URL-конфигурации Django-проекта
│   ├── urls_api_v1.py          # Единый файл URL-конфигурации для REST API v1
│   └── wsgi.py                 # Точка входа WSGI для HTTP-запросов с синхронными обработчиками (WebSockets работать не будут)
│
├── .coveragerc                 # Конфигурация инструмента coverage.py (анализ покрытия кода тестами)
├── .dockerignore               # Исключения при сборке Docker-образа Django-проекта
├── .flake8                     # Настройки линтера Flake8
├── conftest.py                 # Глобальные фикстуры pytest
├── Dockerfile                  # Инструкция multi-stage-сборки Docker-образа Django-проекта
├── factories.py                # Фабрики генерации тестовых данных (Factory Boy)
├── manage.py                   # Управляющий CLI-скрипт Django
├── pyproject.toml              # Настройки black, isort и mypy
├── pytest.ini                  # Конфигурация pytest
├── requirements.base.in        # Базовые (production) зависимости в человекочитаемом формате
├── requirements.base.lock.txt  # Зафиксированные версии базовых (production) зависимостей через pip-tools
├── requirements.dev.in         # Зависимости для разработки (dev) в человекочитаемом формате
├── requirements.dev.lock.txt   # Зафиксированные версии зависимостей для разработки (dev) через pip-tools
└── ...

.env.example                    # Шаблон настройки переменных окружения
.env.test                       # Переменные окружения для тестирования (при CI и при CD)
.pre-commit-config.yaml         # Конфигурация pre-commit гит-хуков
docker-compose.cd-lite.yml      # Дополнительная конфигурация инфраструктуры для CD-тестирования (E2E) облегченной production-сборки (prod-lite)
docker-compose.cd.yml           # Дополнительная конфигурация инфраструктуры для CD-тестирования (E2E) полной production сборки (prod)
docker-compose.dev.yml          # Дополнительная конфигурация инфраструктуры для версии сборки при разработке (dev)
docker-compose.prod-lite.yml    # Дополнительная конфигурация инфраструктуры облегченной production-сборки (prod-lite) для VPS с 1 ГБ RAM
docker-compose.prod.yml         # Дополнительная конфигурация инфраструктуры полной production сборки (prod)
docker-compose.test.yml         # Конфигурация инфраструктуры для CI: black, isort, flake8, mypy и pytest
docker-compose.yml              # Базовая конфигурация инфраструктуры, отдельно не используется, обязательно требуется для dev-, prod- и cd-конфигураций
└── ...
```

## 2. Описание, настройка и запуск сборок проекта

### 2.1 Системные требования для запуска

Для запуска проекта понадобятся:

- [**Docker**](https://docs.docker.com/get-docker/) версии 24+
- [**Docker Compose**](https://docs.docker.com/compose/install/) версии 2.20+ (используется `!override`)

### 2.2 Копирование файлов для запуска

#### Вариант №1: клонирование репозитория. Рекомендуется для разработчиков.

Этот вариант сохраняет всю историю коммитов и позволяет работать с Git (автоматически создается директория .git с Git-историей разработки).

- Установите [**Git**](https://git-scm.com/downloads), если он еще не установлен.
- Склонируйте репозиторий:

```bash
git clone https://github.com/mikhail-sakulin/django-studyoverflow.git
cd django-studyoverflow
```

#### Вариант №2: скачивание архива с исходным кодом из релиза. Рекомендуется только для получения исходного кода без последующей разработки.

> Скачанный архив не содержит служебную директорию .git. История коммитов и работа с Git будут недоступны.

Перейдите на страницу [Releases](https://github.com/mikhail-sakulin/django-studyoverflow/releases), выберите нужную версию и скачайте архив с исходным кодом (**Source code (zip/tar.gz)**), затем распакуйте его.

#### Вариант №3: скачивание из релиза только отдельных файлов без архива. Рекомендуется только для запуска prod-сборки с использованием готовых Docker-образов из GitHub Container Registry (GHCR).

Если вам не нужен исходный код, а требуется только запустить готовую production-сборку с помощью опубликованных Docker-образов проекта, скачайте на странице нужного [релиза](https://github.com/mikhail-sakulin/django-studyoverflow/releases) следующие файлы:

- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env.example.release` — переименуйте в `.env.prod` и заполните своими значениями

Опционально:

- `docker-compose.prod-lite.yml` — если планируется запуск облегченной prod-lite сборки для VPS с ограниченной RAM

### 2.3 Быстрый пробный запуск без предварительной настройки

Если вы хотите быстро запустить проект и проверить его работоспособность без предварительного заполнения `.env` файлов и настройки внешних сервисов (S3, SMTP, OAuth), вы можете переименовать `.env.example` в `.env.prod` — он уже содержит шаблонные значения переменных окружения.

> ⚠️ **Это не полноценный production-запуск.** В `.env.example` используются шаблонные значения (пароли, ключи и так далее), конфигурация не предназначена для доступа извне — не используйте для настоящего развертывания на сервере. Способ подходит только для локальной проверки работоспособности сборки.

Некоторые возможности будут **недоступны** из-за шаблонных значений в `.env.example`:

- отправка email-писем;
- авторизация через OAuth;
- загрузка и хранение файлов через S3 (аватарки).

Порядок запуска:

1) Убедитесь, что установлены необходимые программы из раздела [2.1 Системные требования для запуска](#21-системные-требования-для-запуска).

2) Получите файлы проекта одним из способов из раздела [2.2 Копирование файлов для запуска](#22-копирование-файлов-для-запуска).

3) Скопируйте и переименуйте файл:

```bash
cp .env.example .env.prod
```

4) Запустите production-сборку:

```bash
docker compose -p studyoverflow-demo -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --wait
```

5) После запуска проект будет доступен на `http://localhost/`.

6) Для остановки и удаления пробной сборки вместе с контейнерами и томами (данными) используйте команду:

```bash
docker compose -p studyoverflow-demo -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod down -v
```

### 2.4 Настройка переменных окружения

Проект использует файлы окружения:
- `.env.dev` — для локальной разработки, создается по образцу `.env.example`, используется с `docker-compose.dev.yml`;
- `.env.prod` — для prod и prod-lite сборок, создается по образцу `.env.example`, используется с `docker-compose.prod.yml` и `docker-compose.prod-lite.yml`;
- `.env.test` — используется для CI/CD-пайплайнов (`ci.yml`, `cd-checks.yml`) и для локального запуска тестов через pytest (в том числе в pre-commit). В настройке нуждаются только переменные подключения к БД, их настройка описана в конце этого раздела.

#### Таблица переменных окружения

`Dev` — development-сборка для разработки.

`Prod` — production-сборка, которую можно запускать как локально по HTTP, так и на prod-сервере по HTTPS.

#### Django

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Секретный ключ Django | Любое подходящее значение | Уникальный ключ |
| `DEBUG` | Режим отладки | `True` | `False` |
| `DJANGO_ALLOWED_HOSTS` | Разрешенные хосты | `127.0.0.1,localhost` | Домен/IP сервера |
| `SITE_DOMAIN` | Домен приложения | `localhost` | Реальный домен |
| `CSRF_TRUSTED_ORIGINS` | Доверенные домены для https-запросов | Не задается | Домен по https (если `NGINX_SSL_ENABLED=true`) |

#### Nginx

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `NGINX_SSL_ENABLED` | Включение HTTPS | Не задается (Nginx не используется в dev) | `true` или `false` |

#### Docker

| Переменная | Описание | Dev | Prod (сборка) | Prod (деплой) |
|---|---|---|---|---|
| `STUDYOVERFLOW_IMAGE` | Имя образа приложения | `studyoverflow-backend` | `studyoverflow-backend` | Имя образа из реестра, например `ghcr.io/<владелец_репозитория>/studyoverflow-backend` |
| `NGINX_IMAGE` | Имя образа Nginx | `studyoverflow-nginx` | `studyoverflow-nginx` | Имя образа из реестра |
| `LOKI_IMAGE` | Имя образа Loki | `studyoverflow-loki` | `studyoverflow-loki` | Имя образа из реестра |
| `PROMTAIL_IMAGE` | Имя образа Promtail | `studyoverflow-promtail` | `studyoverflow-promtail` | Имя образа из реестра |
| `GRAFANA_IMAGE` | Имя образа Grafana | `studyoverflow-grafana` | `studyoverflow-grafana` | Имя образа из реестра |
| `IMAGE_TAG` | Тег образов | `dev` | `prod` | `latest` |
| `IMAGE_TAG_CI` | Тег образа приложения для CI-проверок | — | — | — |

> Для Nginx в prod-lite-сборке используется та же переменная `NGINX_IMAGE`, что и в полной prod-сборке — суффикс `-lite` к имени образа добавляется автоматически в `docker-compose.prod-lite.yml` (`image: ${NGINX_IMAGE}-lite:${IMAGE_TAG:-prod}`), отдельная переменная не требуется.

> `IMAGE_TAG_CI` используется только в `docker-compose.test.yml` (проверки в `ci.yml`) и задается только в `.env.test`.

#### PostgreSQL

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `POSTGRES_USER` | Имя пользователя БД | Любое значение | Свое значение |
| `POSTGRES_PASSWORD` | Пароль пользователя БД | Любое значение | Свой пароль |
| `POSTGRES_DB` | Имя базы данных | Любое значение | Свое значение |
| `POSTGRES_HOST` | Хост БД | Не менять | Не менять |
| `POSTGRES_PORT` | Порт БД | Не менять | Не менять |

> В dev-сборке PostgreSQL проброшен на порт `5434` хоста для доступа к БД.

#### Django Superuser

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `DJANGO_SUPERUSER_USERNAME` | Логин суперпользователя | Не обязательно | Свое значение (обязательно) |
| `DJANGO_SUPERUSER_EMAIL` | Email суперпользователя | Не обязательно | Свое значение (обязательно) |
| `DJANGO_SUPERUSER_PASSWORD` | Пароль суперпользователя | Не обязательно | Свой пароль (обязательно) |

> В prod-сборке при старте контейнера-инициализатора `studyoverflow-init` автоматически выполняется кастомная команда `python manage.py create_superuser_from_env`, для которой нужны данные переменные. В dev-сборке контейнера-инициализатора нет, без данных переменных окружения суперпользователя можно создать стандартной Django-командой `python manage.py createsuperuser`.

#### Grafana

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `GF_EXTERNAL_PROTOCOL` | Внешний протокол доступа к Grafana | `http` | `https` или `http`, синхронно с `NGINX_SSL_ENABLED` |
| `GF_SECURITY_ADMIN_USER` | Логин администратора Grafana | Любое значение | Свое значение |
| `GF_SECURITY_ADMIN_PASSWORD` | Пароль администратора Grafana | Любое значение | Свой пароль |

#### Flower

| Переменная | Описание | Dev | Prod |
|---|---|---|---|
| `FLOWER_BASIC_AUTH` | Логин:пароль для Basic Auth панели Flower | Любое значение | Свои логин и пароль |

#### S3 Storage

Хранение медиа-файлов (аватарок) в S3. Без настройки загрузка файлов (аватарок) работать не будет.

| Переменная | Описание | Dev и Prod |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | Ключ доступа S3 | Ключ |
| `AWS_SECRET_ACCESS_KEY` | Секретный ключ S3 | Ключ |
| `AWS_STORAGE_BUCKET_NAME` | Имя бакета S3 | Название бакета |

#### SMTP

Отправка email (восстановление пароля). Без настройки письма отправляться не будут.

| Переменная | Описание | Dev и Prod |
|---|---|---|
| `EMAIL_HOST` | Адрес почтового сервера | Адрес сервера |
| `EMAIL_PORT` | Порт SMTP | Порт |
| `EMAIL_HOST_USER` | Адрес отправителя | Email |
| `EMAIL_HOST_PASSWORD` | Пароль от почты | Пароль |
| `EMAIL_USE_SSL` | Использовать SSL | `True`/`False` |

#### Redis

| Переменная | Описание | Dev и Prod |
|---|---|---|
| `CELERY_BROKER_URL` | Брокер сообщений Celery | Не менять |
| `CELERY_RESULT_BACKEND` | Хранилище результатов Celery | Не менять |
| `REDIS_CHANNELS_URL` | Redis для Django Channels | Не менять |
| `REDIS_CELERY_ONCE_URL` | Redis для блокировок Celery-once | Не менять |
| `REDIS_CACHE_URL` | Redis для кеша Django | Не менять |

#### Social Auth (OAuth)

Авторизация через соцсети. Без настройки авторизация через соцсети работать не будет.

| Переменная | Описание | Dev и Prod | Где получить |
|---|---|---|---|
| `SOCIAL_AUTH_GITHUB_ID` | ID GitHub OAuth App | ID приложения | [GitHub Developer Settings](https://github.com/settings/developers) |
| `SOCIAL_AUTH_GITHUB_SECRET` | Ключ GitHub OAuth App | Ключ | [GitHub Developer Settings](https://github.com/settings/developers) |
| `SOCIAL_AUTH_GOOGLE_ID` | ID Google OAuth App | ID приложения | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `SOCIAL_AUTH_GOOGLE_SECRET` | Ключ Google OAuth App | Ключ | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `SOCIAL_AUTH_YANDEX_ID` | ID Яндекс OAuth App | ID приложения | [Яндекс OAuth](https://oauth.yandex.ru/) |
| `SOCIAL_AUTH_YANDEX_SECRET` | Ключ Яндекс OAuth App | Ключ | [Яндекс OAuth](https://oauth.yandex.ru/) |
| `SOCIAL_AUTH_VK_ID` | ID VK OAuth App | ID приложения | [VK Apps](https://vk.com/apps?act=manage) |
| `SOCIAL_AUTH_VK_SECRET` | Ключ VK OAuth App | Ключ | [VK Apps](https://vk.com/apps?act=manage) |

> В соответствии с ФЗ №149 авторизация через сервисы GitHub и Google должна быть недоступна для пользователей.

#### Переменные БД из `.env.test` для локального запуска тестов

Django-настройки проекта всегда читают `.env.test` (в `settings/base.py`) независимо от режима запуска — это сделано для удобного локального запуска тестов через `pytest` (в том числе в pre-commit хуках) с помощью БД на хосте без поднятия Docker-контейнеров. В настройке нуждаются только переменные подключения к БД, можно задать как подключение к БД хоста, так и сменить на подключение к БД Docker-контейнера, например из dev-сборки.

Для переменных `POSTGRES_HOST` и `POSTGRES_PORT` есть два варианта настроек для локального запуска тестов:

- **Без Docker** (нужен Python с зависимости проекта, установленными на хосте, а также БД на хосте): укажите в `.env.test` подключение к вашей локальной PostgreSQL, например:
  `POSTGRES_HOST=localhost`
  `POSTGRES_PORT=5432`

- **Через Docker** (на хосте ничего устанавливать не потребуется, но тесты нужно будет запускать внутри контейнера, например через `docker compose -p studyoverflow-test -f docker-compose.test.yml --env-file .env.test run --rm studyoverflow-tests`): укажите имя и порт сервиса PostgreSQL из Docker Compose:
  `POSTGRES_HOST=postgres`
  `POSTGRES_PORT=5432`

### 2.5 Особенности и настройка dev-сборки

Dev-сборка предназначена для локальной разработки: код Django-проекта запускается через команду `python manage.py runserver 0.0.0.0:8000`, используя встроенный сервер разработки Django, Nginx в этой сборке нет. Код проекта монтируется с хоста в контейнеры с Django-проектом (`studyoverflow-1`, `celery-worker` и `celery-beat`).

Дополнительные (по сравнению с prod-сборкой) зависимости для разработки в человекочитаемом виде с комментариями перечислены в файле `studyoverflow/requirements.dev.in`.

В dev-сборке запускаются следующие сервисы:

- `studyoverflow-1` — Django-проект, запущенный через `manage.py runserver`;
- `postgres` — база данных PostgreSQL;
- `redis` — брокер сообщений Celery, также используется для Django Channels, Celery-Once и кеша;
- `celery-worker` — обработчик асинхронных задач Celery;
- `celery-beat` — планировщик периодических задач Celery;
- `promtail` — агент сбора логов Docker-контейнеров и отправки их в Loki;
- `loki` — хранилище логов;
- `grafana` — веб-интерфейс для просмотра и поиска логов;
- `adminer` — веб-интерфейс для просмотра и управления БД PostgreSQL;
- `flower` — веб-интерфейс для мониторинга задач и очередей Celery.

При запуске dev-сборки заняты следующие порты на хосте (при конфликте их можно заменить в `docker-compose.dev.yml`):

- `8000` — Django-приложение
- `5434` — PostgreSQL
- `9080` — Promtail
- `3100` — Loki
- `3000` — Grafana
- `8081` — Adminer
- `5555` — Flower

Код проекта монтируется с хоста в контейнеры `studyoverflow-1`, `celery-worker` и `celery-beat`, поэтому изменения в коде появляются в данных контейнерах без пересборки образа при перезапуске контейнеров. Благодаря запуску Django-проекта через `manage.py runserver` контейнер `studyoverflow-1` перезапускается автоматически при изменении Python-кода. При этом контейнеры с Celery-процессами нужно перезапускать вручную для применения изменений, например командой:

```bash
docker compose -p studyoverflow-dev -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev restart celery-worker celery-beat
```

Применение миграций БД и создание суперпользователя описаны в [пункте 5](#dev-migrate-superuser) раздела [2.6 Запуск dev-сборки](#26-запуск-dev-сборки).

### 2.6 Запуск dev-сборки

1) Убедитесь, что установлены необходимые программы из раздела [2.1 Системные требования для запуска](#21-системные-требования-для-запуска).

2) Получите файлы проекта из раздела [2.2 Копирование файлов для запуска](#22-копирование-файлов-для-запуска) обязательно через Вариант №1 (git clone), чтобы была доступна история коммитов и работа с Git для последующей разработки.

3) Создайте файл `.env.dev` и настройте переменные окружения согласно разделу [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения) для dev-сборки.

4) Запустите dev-сборку:

Без флага `-d`, чтобы логи контейнеров выводились в терминал (терминал будет занят):

```bash
docker compose -p studyoverflow-dev -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up
```

С флагом `-d`, чтобы запустить контейнеры в фоновом режиме (терминал останется свободным), и флагом `--wait`, чтобы дождаться запуска всех контейнеров:

```bash
docker compose -p studyoverflow-dev -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d --wait
```

5) <a name="dev-migrate-superuser"></a>В dev-сборке нет `studyoverflow-init`-контейнера, который в prod-сборке автоматически выполняет миграции, создает суперпользователя и собирает статику (не нужно в dev), поэтому эти шаги нужно выполнить вручную (в новом терминале, если в пункте `4` запуск dev-сборки был без флага `-d`):

Применение миграций БД:

```bash
docker compose -p studyoverflow-dev exec studyoverflow-1 python manage.py migrate
```

Создание суперпользователя (только если заданы необходимые переменные окружения) через кастомную команду create_superuser_from_env, используя данные из переменных окружения:

```bash
docker compose -p studyoverflow-dev exec studyoverflow-1 python manage.py create_superuser_from_env
```

Если вы не задавали данные суперпользователя в переменных окружения в `.env.dev` файле, то используйте стандартную Django-команду:

```bash
docker compose -p studyoverflow-dev exec -it studyoverflow-1 python manage.py createsuperuser
```

6) После запуска проект будет доступен на `http://localhost:8000/`.

7) Для остановки dev-сборки и удаления контейнеров (Docker-тома не удаляются) используйте команду:

```bash
docker compose -p studyoverflow-dev -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev down
```

### 2.7 Особенности и настройка prod- и prod-lite-сборок

Prod-сборка предназначена для полноценного развертывания проекта на сервере, но ее также можно запускать локально: Django-приложение запускается через ASGI-сервер `Daphne` (нужен для поддержки WebSockets через Django Channels), перед приложением стоит Nginx в качестве reverse-proxy, балансировщика запросов между контейнерами с бекендом и раздатчика статики. Миграции и создание суперпользователя выполняются автоматически при запуске сборки через контейнер-инициализатор `studyoverflow-init`. Через настройку переменных окружения prod-сборку можно запускать как по HTTP (например локально), так и по HTTPS (например на сервере). Подробнее про автоматическую конфигурацию Nginx в зависимости от нужного протокола описано в соответствующем разделе.

> Prod-сборка для запуска требует сервер с 2 Гб RAM минимум, для запуска на сервере с 1 Гб RAM используйте prod-lite-сборку.

В prod-сборке запускаются следующие сервисы:

- `studyoverflow-init` — контейнер-инициализатор, который перед стартом остальных сервисов с Django-проектом выполняет миграции БД, создает суперпользователя (через кастомную команду `create_superuser_from_env`) и собирает статику, контейнер останавливается после выполнения команд;
- `studyoverflow-1`, `studyoverflow-2` — два экземпляра бекенда с Django-приложением, запущенные через `Daphne`;
- `postgres` — база данных PostgreSQL;
- `redis` — брокер сообщений Celery, также используется для Django Channels, Celery-Once и кеша;
- `celery-worker` — обработчик асинхронных задач Celery;
- `celery-beat` — планировщик периодических задач Celery;
- `nginx` — reverse-proxy, балансировщик и отдатчик статики, принимает запросы из внешней сети (единственный сервис с портами, проброшенными на хост);
- `certbot` — получение и продление SSL-сертификатов Let's Encrypt для Nginx (подробнее о настройке HTTP/HTTPS — в отдельном разделе);
- `promtail` — агент сбора логов Docker-контейнеров и отправки их в Loki;
- `loki` — хранилище логов;
- `grafana` — веб-интерфейс для просмотра и поиска логов;
- `adminer` — веб-интерфейс для просмотра и управления БД PostgreSQL;
- `flower` — веб-интерфейс для мониторинга задач и очередей Celery.

В отличие от dev-сборки, на хост в prod-сборке проброшены только порты `80` (HTTP) или `443` (HTTPS) у сервиса `nginx` (порты должны быть свободными на хосте) — все остальные сервисы (включая Adminer, Grafana и Flower) доступны напрямую только внутри Docker-сети. Через Nginx по вложенным путям `/grafana/`, `/flower/` и `/adminer/` доступны соответствующие сервисы, запросы к бекенду также проксируются через Nginx.

#### Особенности prod-lite-сборки

Prod-lite — облегченный вариант prod-сборки для VPS с ограниченной RAM (1 Гб), запускается через дополнительный файл `docker-compose.prod-lite.yml` поверх обычной prod-сборки. Отличия от полной prod-сборки:

- `studyoverflow-2` не запускается (доступен только один экземпляр бекенда — `studyoverflow-1`);
- `celery-worker` запускается с флагами `--pool=prefork --concurrency=1 --max-memory-per-child=130000`, запускающими только один экземпляр Celery-воркера в отдельном дочернем процессе (при этом запускается Master-процесс независимо от настроек) с ограниченным потреблением RAM;
- `promtail`, `loki`, `grafana` и `flower` не запускаются (отключены для экономии RAM);
- `nginx` собирается из отдельного `Dockerfile-lite` и зависит только от `studyoverflow-1` (без `studyoverflow-2`, остальные отключенные сервисы также удалены из lite-конфигурации Nginx).

Отключение сервисов `studyoverflow-2`, `promtail`, `loki`, `grafana` и `flower` в prod-lite-сборке реализовано через Docker Compose profiles (`backend-2` и `monitoring`), но на данный момент включить эти сервисы обратно через `--profile` при запуске **не получится** — конфигурация `nginx-lite` не настроена на работу со `studyoverflow-2` и с путями `/grafana/` и `/flower/` (profiles используется только для самого механизма отключения сервисов).

### 2.8 Запуск prod- и prod-lite-сборок

1) Убедитесь, что установлены необходимые программы из раздела [2.1 Системные требования для запуска](#21-системные-требования-для-запуска).

2) Получите файлы проекта одним из способов из раздела [2.2 Копирование файлов для запуска](#22-копирование-файлов-для-запуска).

3) Создайте файл `.env.prod` и настройте переменные окружения согласно разделу [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения) для prod-сборки.

4) Запустите нужный вариант сборки:

Полная prod-сборка:

```bash
docker compose -p studyoverflow-prod -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --wait
```

Prod-lite-сборка:

```bash
docker compose -p studyoverflow-prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-lite.yml --env-file .env.prod up -d --wait
```

5) В отличие от dev-сборки, миграции БД, создание суперпользователя и сборка статики выполняются автоматически контейнером `studyoverflow-init` при старте сборки (останавливается после выполнения команд) — вручную выполнять эти шаги не нужно.

6) После запуска проект будет доступен на `http://localhost/` при запуске по протоколу HTTP или на настроенном домене при работе по HTTPS.

7) Для остановки сборки и удаления контейнеров (Docker-тома не удаляются) используйте команду с тем же набором `-f` файлов, что и при запуске.

Для полной prod-сборки:

```bash
docker compose -p studyoverflow-prod -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod down
```

Для prod-lite-сборки:

```bash
docker compose -p studyoverflow-prod -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-lite.yml --env-file .env.prod down
```

## 3. Настройка HTTP/HTTPS в Nginx, использование Certbot

### 3.1 Логика выбора HTTP- и HTTPS-конфигураций Nginx

Nginx в prod- и prod-lite-сборках выполняет роль reverse-proxy: принимает входящие запросы из внешней сети (единственный сервис с портами, проброшенными на хост), проксирует их на бекенд с Django-проектом, на другие сервисы и раздает статику (устройство prod- и prod-lite-сборок описано в разделе [2.7 Особенности и настройка prod- и prod-lite-сборок](#27-особенности-и-настройка-prod--и-prod-lite-сборок)). Через настройку переменных окружения Nginx можно запускать как по HTTP (например, локально) на 80-ом порту, так и по HTTPS (например, на production-сервере) на 443-ем порту, что автоматически реализуется благодаря shell-скриптам.

Используются два отдельных Docker-образа Nginx:

- `nginx/Dockerfile` — для обычной prod-сборки;
- `nginx/Dockerfile-lite` — для prod-lite-сборки, которая зависит только от `studyoverflow-1` (один сервис бекенда) и не содержит путей `/grafana/` и `/flower/`.

Внутрь каждого образа скопированы две конфигурации:

Для `Dockerfile` (prod-сборка):

- `http.conf` — для работы по HTTP;
- `https.conf` — для работы по HTTPS.

Для `Dockerfile-lite` (prod-lite-сборка):

- `http-lite.conf` — для работы по HTTP;
- `https-lite.conf` — для работы по HTTPS.

В каждом образе есть свой shell-скрипт инициализации контейнера (`entrypoint.sh` для prod, `entrypoint-lite.sh` для prod-lite), заданный как `ENTRYPOINT` образа, который выбирает нужную конфигурацию для HTTP или для HTTPS:

1) удаляются старые конфигурации из `/etc/nginx/conf.d/`;
2) в зависимости от значения переменной окружения `NGINX_SSL_ENABLED` (`true`/`True` — HTTPS, иначе — HTTP) нужный конфиг копируется в `/etc/nginx/conf.d/default.conf`;
3) Nginx запускается в foreground-режиме (`nginx -g "daemon off;"`) — `exec` заменяет процесс скрипта процессом Nginx с тем же PID, чтобы Docker мог получать от него сигналы и не считал контейнер завершенным.

> Настройка переменных окружения, связанных с HTTP/HTTPS-режимами Nginx, описана в разделе [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения): `NGINX_SSL_ENABLED`, а также связанные с ней `GF_EXTERNAL_PROTOCOL` и `CSRF_TRUSTED_ORIGINS`.

В результате данной логики один и тот же Docker-образ Nginx подходит для запуска сборок как по HTTP, так и по HTTPS без пересборки образа, переключение происходит только через переменную окружения `NGINX_SSL_ENABLED`.

### 3.2 Использование Certbot для получения и продления SSL-сертификатов

[**Certbot**](https://certbot.eff.org/) — консольный клиент [Let's Encrypt](https://letsencrypt.org/), бесплатного удостоверяющего центра, который выпускает и подтверждает SSL-сертификаты для доменов. Сертификат нужен, чтобы сайт мог работать по HTTPS.

В `docker-compose.prod.yml` для этого используется сервис `certbot`. В контейнере задан бесконечный цикл ожидания в `entrypoint` для выполнения периодической команды `certbot`. Процесс выпуска и продления сертификата:

- Certbot использует **webroot-плагин**: он создает временный файл-подтверждение в общем с Nginx томе (`certbot-webroot`), а Let's Encrypt обращается к этому файлу через порт `80` — удостоверяющий центр убеждается, что домен указывает на данный сервер.
- после успешной проверки Certbot сохраняет сертификат и приватный ключ в том `certbot-etc`, смонтированный также в контейнер с Nginx для работы по HTTPS.
- на сервере настраивается периодическая задача `cron`, которая регулярно выполняет `certbot renew` (продление SSL-сертификата, так как сертификаты Let's Encrypt действуют 90 дней) внутри уже запущенного контейнера и перезагружает Nginx для обновления файлов.

На новом сервере при первом запуске получить сертификат нужно вручную. Для первого получения сертификата Nginx должен работать по HTTP, так как его запуск по HTTPS требует наличия текущих файлов сертификата на диске. При этом для обновления сертификата (файлы сертификата уже есть на диске для HTTPS) в HTTPS-конфигурации предусмотрен специальный маршрут на 80-ом порту `/.well-known/acme-challenge/`.

<details>
<summary>Инструкция первого получения сертификата на новом сервере и настройки его автопродления на Linux</summary>

1) Остановить запущенную сборку (если она уже запущена):

```bash
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  down
```

2) Запустить сборку с `NGINX_SSL_ENABLED=false`, чтобы Nginx поднялся по HTTP и мог ответить на проверку от Let's Encrypt:

```bash
NGINX_SSL_ENABLED=false \
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  up -d
```

3) Получить сертификат в первый раз (entrypoint контейнера `certbot` переопределяется, чтобы выполнить команду `certbot` напрямую, а не запускать цикл ожидания), в команде укажите ваш домен с "www" и без, а также email, который передастся центру сертификации Let's Encrypt для уведомлений:

```bash
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  run --rm --entrypoint "" certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d ваш_домен -d www.ваш_домен \
  --email ваш_email \
  --agree-tos --no-eff-email \
  --verbose --non-interactive
```

4) Остановить сборку:

```bash
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  down
```

5) Запустить сборку заново (с `NGINX_SSL_ENABLED=true` в `.env.prod`), чтобы Nginx применил HTTPS-конфигурацию с выпущенным сертификатом:

```bash
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  up -d
```

6) Проверить, что автопродление работает корректно, без реального обновления файлов сертификата (флаг `--dry-run`):

```bash
docker compose -p studyoverflow-prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  run --rm --entrypoint "" certbot certbot renew --dry-run
```

7) Настроить автопродление через `cron` (планировщик задач на Linux) — сертификат действует 90 дней, Let's Encrypt разрешает продление начиная с 30 дней до истечения срока, задача запускается дважды в день:

```bash
crontab -e
```

Добавить периодическую задачу — запуск в 3:00 и 15:00 — команда заходит в уже работающий контейнер `certbot`, при необходимости продлевает сертификат и перезагружает Nginx, чтобы он имел доступ к обновленным файлам:

```bash
0 3,15 * * * cd /app/studyoverflow && \
  docker compose -p studyoverflow-prod \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    --env-file .env.prod \
    exec -T certbot certbot renew --quiet && \
  docker compose -p studyoverflow-prod \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    --env-file .env.prod \
    exec -T nginx nginx -s reload
```

Сохранить и выйти (`Ctrl+O`, `Enter`, затем `Ctrl+X`).

8) Проверить, что задача добавлена:

```bash
crontab -l
```

Если используется prod-lite-сборка, добавьте `-f docker-compose.prod-lite.yml` к каждой Docker Compose-команде.

</details>

## 4. Особенности Django-проекта

### 4.1 ER-диаграмма кастомных Django-моделей

В Django-проекте используются 4 кастомных приложения: `navigation`, `users`, `posts` и `notifications`.

ER-диаграмма кастомных Django-моделей проекта (и стандартной django_content_type) и связей между ними:

<img width="1648" height="1429" alt="dbdiagram-download" src="https://github.com/user-attachments/assets/3b04a4a4-9c52-4704-9878-b462fdd76138" />

#### Дополнения к ER-диаграмме

**1) Generic-связи (`content_type` + `object_id`)**

В моделях используется `GenericForeignKey` — универсальный внешний ключ (инструмент ORM Django), позволяющий связывать одну модель с любой другой моделью. Вместо жесткой привязки к конкретной таблице БД он формирует динамическую связь на основе **пары полей**: `content_type_id` (указывает на тип целевой модели в служебной таблице `django_content_type`) и `object_id` (хранит первичный ключ конкретной записи этой модели). За счет разных значений `content_type_id` одна модель может иметь Generic-связь сразу с несколькими моделями. В проекте используются:

- Универсальные лайки `posts_like` — модель содержит `GenericForeignKey` (`content_type_id` + `object_id`), что позволяет связать лайки сразу с двумя разными сущностями: постами `posts_post` и комментариями `posts_comment`.
- Универсальная система уведомлений `notifications_notification` — модель через `GenericForeignKey` (`content_type_id` + `object_id`) связывается с любой сущностью системы, ставшей объектом уведомления (например, пост `posts_post`, комментарий `posts_comment`, лайк `posts_like` и так далее).
- Промежуточная модель для связи тегов с постами `posts_taggedpost` — модель (наследуется от taggit.models.GenericTaggedItemBase) использует `GenericForeignKey` (`content_type_id` + `object_id`) для привязки нормализованных тегов `posts_lowercasetag` к постам `posts_post`.
- В моделях `posts_post`, `posts_comment` и `posts_like` на уровне ORM объявлены обратные связи `GenericRelation` (тоже инструмент ORM Django), которые позволяют обращаться к связанным через `GenericForeignKey` сущностям (лайкам или уведомлениям) в Python-коде без ручной фильтрации по `ContentType`, а также обеспечивают каскадное удаление (лайков и уведомлений) при удалении постов и комментариев, чего бы не было без `GenericRelation` (уведомления и лайки не удалялись бы автоматически через каскадное удаление).

**2) UniqueConstraint для username и email**

1. Модель `User` (`users_user`) помимо `unique=True` на самом поле `username` использует отдельный constraint для уникальности `username` в верхнем регистре:

```python
models.UniqueConstraint(
    Upper("username"),
    name="unique_user_uppercase_username",
),
```

Это нужно для уникальности `username` на уровне БД независимо от регистра, нельзя создать двух пользователей `Root` и `root` одновременно. Также при этом создается индекс БД для Upper-значений поля, что используется при регистроНЕзависимом поиске при использовании лукапа `iexact`.

2. Модель `User` (`users_user`) вместо `unique=True` на самом поле `email` использует только отдельный constraint для уникальности `email` в верхнем регистре:

```python
models.UniqueConstraint(
    Upper("email"),
    name="unique_user_uppercase_email",
),
```

Это нужно, чтобы, например, `Ivan@example.com` и `ivan@example.com` считались одним и тем же email на уровне БД. На самом поле не задан `unique=True`, поскольку поиск email осуществляется только без учета регистра (iexact).

**3) Другие unique constraints**

- `posts_like`: `unique_together = ("user", "content_type", "object_id")` — пользователь не может поставить лайк одному и тому же объекту дважды;
- `posts_taggedpost`: `unique_together = ("tag", "content_type", "object_id")` — исключает дублирование одного и того же тега у поста.

### 4.2 Кастомные Django-приложения

<img width="1733" height="1295" alt="django-apps-2" src="https://github.com/user-attachments/assets/68cbbd82-8a44-4e52-ae5c-5929e04c0e2d" />

**1) Приложение `navigation`**

Приложение выполняет роли core и navigation модулей проекта: в него вынесена общая логика, не привязанная к другим приложениям. Своих моделей приложение не имеет.

В приложении реализовано:
- общие для всего проекта HTML-шаблоны и статика: базовый шаблон с подключением Bootstrap и JS-скрипта для WebSocket, header и footer — компоненты навигации, блок всплывающих сообщений Django;
- главная страница и `health`-эндпоинт (healthcheck);
- кастомные обработчики HTTP-ошибок (400/403/404/500);
- единый список пунктов меню, переиспользуемый в header и footer через шаблонный тег;
- sitemap для главной страницы, списка постов и списка пользователей;
- middleware логирования активности пользователей и определения источника запроса (web/api) для логирования другими приложениями;
- сигнал, синхронизирующий домен `Site` с переменной окружения `SITE_DOMAIN` после каждой миграции;
- кастомные схемы аутентификации для `drf-spectacular` для корректного отображения всех методов API-аутентификации (сессия, DRF-токен, JWT) в Swagger;
- интеграционные тесты взаимодействия объектов моделей Django-проекта.

**2) Приложение `users`**

Приложение отвечает за пользователей проекта: регистрацию, аутентификацию (в том числе OAuth), профиль, аватары, роли пользователей и модерацию (блокировку) аккаунтов. Также содержит соответствующие HTML-шаблоны, статику и REST API.

В приложении задана кастомная модель `User` — расширяет `AbstractUser` полями роли, аватаров, денормализованных счетчиков, блокировки и другими (подробнее на ER-диаграмме или в коде проекта).

Также создан кастомный менеджер пользователей `CustomUserManager`, позволяющий искать пользователя как по username, так и по email (переопределяется метод `get_by_natural_key`).

В приложении реализовано:
- регистрация и вход по логину и паролю, а также вход через OAuth;
- кастомные бекенды аутентификации, дополнительно проверяющие, что пользователь не заблокирован;
- адаптеры `django-allauth`, подставляющие корректные данные профиля из ответа соцсети;
- валидация, загрузка, и удаление аватаров при помощи S3-хранилища, а также обработка изображений (генерация миниатюр) и соответствующие асинхронные Celery-задачи;
- система ролей пользователей и модерации контента, автоматическая синхронизация ролей с группами Django и правами доступа, принудительный выход заблокированных пользователей через middleware (в данной версии проекта не отрабатывает из-за наличия кастомных бекендов аутентификации);
- онлайн-статус пользователей через Redis с синхронизацией значений в БД (поле `last_seen`) через периодическую Celery-задачу;
- подсчет денормализованных счетчиков модели `User` `posts_count`, `comments_count` и `reputation` через обработчики Django-сигналов; 
- синхронизация денормализованных счетчиков со значениями из БД через периодическую Celery-задачу;
- восстановление пароля по email, смена пароля;
- кастомные валидаторы полей модели `User`;
- сервисный слой с бизнес-логикой и инфраструктурой (работа с аватарами и S3, кеширование, обработка изображений, модерация, permissions, онлайн-статус, поля-счетчики модели `User`, валидаторы);
- web-views и api-views, использующие единый сервисный слой, а также общие миксины для представлений;
- обработчики Django-сигналов (с использованием сервисного слоя) для логирования, управления кешем и online-статусом пользователей, настройки прав при миграциях и очистки S3-хранилища при удалении аккаунта;
- асинхронные Celery-задачи (с использованием сервисного слоя) для генерации и удаления миниатюр аватаров, отправки e-mail для сброса пароля, синхронизации денормализованных полей-счетчиков с БД, очистка истекших сессий и JWT-токенов;
- REST API с кастомными классами аутентификации для сессии, DRF-токена и JWT, permissions, OpenAPI-схемами, сериализаторами и api-views;
- модальное окно с полноразмерным аватаром пользователя, открываемое по клику на миниатюру с отложенной загрузкой изображения до клика;
- страница списка пользователей с возможностью фильтрации и сортировки, с загрузкой новых пользователей без перезагрузки страницы с помощью htmx;
- модульные и интеграционные тесты;
- кастомизация админ-панели.

**3) Приложение `posts`**

Приложение содержит посты, теги, комментарии и лайки, а также логику работы с ними, в том числе HTML-шаблоны со статикой вместе с htmx и REST API.

В приложении заданы модели `Post`, `Comment`, универсальная модель `Like` и модели тегов `LowercaseTag` и `TaggedPost` на основе `django-taggit` (подробнее на ER-диаграмме или в коде проекта).

В приложении реализовано:
- рендеринг Markdown в безопасный HTML при создании или изменении (содержимого) поста или комментария (`markdown2` + `bleach`), с защитой math-блоков LaTeX от искажения при рендеринге;
- CRUD-операции с постами и комментариями, включая вложенные (древовидные) комментарии с валидацией иерархии (`parent_comment`/`reply_to`);
- лайки постов и комментариев через единую модель `Like`;
- кастомный лукап ORM `ilike_icontains` для PostgreSQL;
- GIN-индекс с расширением pg_trgm для полей `title` и `search_content` модели `Post`;
- сервисный слой с бизнес-логикой и инфраструктурой (кеширование, переключение лайков, логирование, обработка текста, валидаторы);
- фильтрация и сортировка постов и комментариев c оптимизацией SQL-запросов через общие для web- и api-views миксины;
- работа с тегами: валидация и нормализация введенных тегов;
- подсчет денормализованных счетчиков моделей `Post` и `Comment` через обработчики Django-сигналов;
- синхронизация денормализованных счетчиков моделей `Post` и `Comment` со значениями из БД через асинхронные Celery-задачи;
- обработчики Django-сигналов (с использованием сервисного слоя) для изменения денормализованных полей-счетчиков пользователя, постов и комментариев (счетчики лайков, постов и комментариев), а также инвалидации кеша постов и списков тегов при их изменении;
- асинхронные Celery-задачи для периодического перерасчета и синхронизации счетчиков лайков и комментариев у постов и комментариев через оптимизированные SQL-запросы;
- web-views и api-views, использующие единый сервисный слой, а также общие миксины для представлений;
- REST API с permissions, OpenAPI-схемами, сериализаторами и api-views;
- модульные и интеграционные тесты;
- кастомизация админ-панели;
- на стороне фронтенда:
  - предпросмотр Markdown и LaTeX при создании/редактировании поста без обращения к серверу (JS-библиотека `markdown-it`);
  - подсветка синтаксиса кода через `highlight.js` (в предпросмотре, в опубликованных постах/комментариях и после каждого HTMX-обновления);
  - рендеринг формул через `KaTeX`;
  - выбор тегов из готового списка с поиском;
  - фильтрация и сортировка списка постов;
  - сортировка комментариев без перезагрузки страницы с помощью htmx;
  - работа с htmx: CRUD-операции с комментариями и лайками без перезагрузки страницы.

**4) Приложение `notifications`**

Приложение отвечает за систему уведомлений пользователей о событиях, включая доставку уведомлений в реальном времени через WebSocket, а также содержит соответствующие HTML-шаблоны, статику и REST API.

В приложении задана универсальная модель `Notification`, связывающаяся с любой сущностью проекта, ставшей объектом уведомления (пост, комментарий, лайк, пользователь).

В приложении реализовано:
- создание уведомлений о лайках, постах, комментариях и регистрации пользователя через обработчики Django-сигналов, формирующие данные для уведомления (через сервисный слой) и запускающие асинхронную Celery-задачу создания уведомления после фиксации транзакции;
- обновление счетчика непрочитанных уведомлений и флага обновления списка в реальном времени через Django Channels (WebSocket-соединение) с помощью асинхронной Celery-задачи (защищена от дублирования через `celery_once`), отправляющей событие в соответствующую Django Channels-группу;
- отслеживание онлайн-статуса пользователя через heartbeat-сообщения WebSocket-консьюмера;
- сервисный слой с обработчиками создания уведомлений;
- операции прочтения и удаления уведомлений, включая массовые операции, с оптимизацией количества запускаемых Celery-задач и WebSocket-событий;
- оптимизация SQL-запросов при получении списка уведомлений через общий для web- и api-views миксин (`select_related`, `only`, `GenericPrefetch`);
- web-views для страницы и карточек уведомлений, в том числе обработчики htmx-запросов;
- REST API с OpenAPI-схемами, сериализаторами и api-views;
- обработчики Django-сигналов для инициации создания уведомлений (через сервисный слой) при событиях (лайки, посты, комментарии, регистрация) и логирование их создания;
- асинхронные Celery-задачи для проверки и создания объектов уведомлений, а также отправки обновлений счетчика и списка уведомлений в реальном времени в Django Channels-группу пользователя (с защитой от дублирования через `celery_once`);
- модульные и интеграционные тесты;
- кастомизация админ-панели;
- на стороне фронтенда:
  - загрузка списка уведомлений без перезагрузки страницы с помощью htmx;
  - операции с уведомлениями (прочтение и удаление) без перезагрузки страницы с помощью htmx;
  - обновление счетчика непрочитанных уведомлений в реальном времени через WebSocket-соединение.

### 4.3 Система уведомлений

<img width="1715" height="1016" alt="notifications" src="https://github.com/user-attachments/assets/c1d5ef36-98c8-4082-ac3e-49757d86c592" />

#### Универсальность уведомлений

Уведомления реализованы через универсальную модель `Notification`, которая с помощью `GenericForeignKey` (`content_type` + `object_id`) может ссылаться на любую сущность проекта, ставшую поводом для уведомления. Типы уведомлений заданы следующие:

```python
class NotificationType(models.TextChoices):
    """
    Перечисление типов уведомлений.
    """

    LIKE_POST = "like_post", "Лайк поста"
    LIKE_COMMENT = "like_comment", "Лайк комментария"
    POST = "post_created", "Пост создан"
    COMMENT = "comment_post", "Комментарий к посту"
    REPLY = "reply_comment", "Ответ на комментарий"
    REGISTER = "user_register", "Регистрация пользователя"
```

Благодаря универсальному внешнему ключу (`GenericForeignKey`) одна и та же модель используется для создания уведомления для всех перечисленных событий без необходимости заводить отдельную модель под каждый тип события.

#### Создание уведомлений

Уведомления создаются только через Django-сигналы. К сигналу `post_save` моделей `Like`, `Post`, `Comment` и `User` (в `notifications/signals.py`) подключены обработчики, которые при создании нового объекта (`created=True`, без `raw`-фикстур) вызывают соответствующий хендлер из сервисного слоя (`notifications/services/notification_handlers.py`). Хендлер не создает уведомление напрямую, а задает сообщение и другие данные будущего уведомления, после чего через `transaction.on_commit` ставит в очередь Celery-задачу `create_notification`, которая уже сама создает запись `Notification` в БД. Внутри Celery-задачи дополнительно проверяется существование связанного объекта через `select_for_update` — это защита от гонки состояний, чтобы связанный объект не был удален во время создания уведомления. Через `select_for_update` запись для связанного объекта блокируется в БД до момента создания уведомления.

Разделение (сигнал > сервисный хендлер > Celery-задача) сделано специально для имитации более тяжелой асинхронной работы: в Celery-задаче могла бы быть отправка письма или запроса во внешний сервис. Подобная операция могла бы выполняться долго, и без вынесения в Celery-задачу она бы блокировала основной запрос и заставляла пользователя ждать. В текущем виде создание записи в БД — операция быстрая, и ее можно было бы выполнить синхронно в обработчике сигнала, без Celery, но вынесение в Celery-задачу сохраняет архитектуру, пригодную для замены на более сложную логику уведомлений при надобности.

#### Доставка уведомлений в реальном времени через WebSocket-соединение

За доставку уведомлений в реальном времени отвечает Django Channels (WebSocket). При создании (`post_save`) или удалении (`post_delete`) объекта `Notification` срабатывает сигнал, который вызывает `handle_send_channel_notify_event` — он через `transaction.on_commit` запускает Celery-задачу `send_channel_notify_event`, передавая `user_id` получателя, флаг `update_list` (нужно ли клиенту перезапрашивать список уведомлений) и `reason` (причина события). Задача пересчитывает актуальное количество непрочитанных уведомлений пользователя и отправляет его через `channel_layer.group_send` в Channels-группу `user_{user_id}`, к которой подключены все активные WebSocket-соединения этого пользователя. Консьюмер `NotificationConsumer.notify` получает это групповое событие и пересылает данные клиенту по WebSocket в виде JSON (`unread_notifications_count`, `update_list`, `reason`).

Задача `send_channel_notify_event` защищена от множественных дублирований библиотекой `celery_once` с ключом блокировки по `user_id`: пока для конкретного пользователя выполняется одна такая задача, повторные вызовы (например, при массовых операциях) не добавляются в очередь заново, а игнорируются (`graceful=True`, без выброса исключения). Это защищает от порождения дублирующих Celery-задач и WebSocket-сообщений.

Реализовано различение причины удаления уведомления. Если пользователь удаляет уведомление вручную (через соответствующие web-views или api-views), список уведомлений на клиенте обновлять не нужно (карточка уже удалена с запросом через htmx и скрыта JS-кодом). Но если уведомление удаляется каскадно (например, пользователь удалил пост, с которым было связано чужое уведомление), то список нужно обновить принудительно (если открыт список уведомлений — проверяется у клиента), так как клиент не знает о таком удалении. Чтобы обработчик сигнала `post_delete` (глобальный на весь процесс) мог различать эти два случая (небезопасный в многопоточном режиме `signal.disconnect` нельзя использовать), используется `contextvars.ContextVar` (`notification_delete_reason`): перед удалением уведомления (в web-views или api-views) в переменную контекста устанавливается значение `"self_delete"`, обработчик сигнала читает это значение и решает, отправлять ли клиенту флаг `update_list=True`. `ContextVar` изолирован в рамках одного запроса/потока, поэтому конкурентные запросы разных пользователей не влияют друг на друга.

#### Логика на фронтенде

При загрузке страницы устанавливается единое WebSocket-соединение (`websocket_notifications.js`) по адресу `ws/notifications/`. Consumer при подключении добавляет канал в группу пользователя и отмечает его онлайн-статус. Клиент, в свою очередь, раз в минуту отправляет серверу heartbeat-сообщение (`{"type": "heartbeat"}`), чтобы онлайн-статус пользователя оставался актуальным, пока открыта вкладка. WebSocket-соединение закрывается при закрытии страницы и открывается заново при загрузке новой. При закрытии соединения канал удаляется из группы пользователя.

Если сервер по WebSocket-соединению прислал флаг `update_list: true` и на странице присутствует список уведомлений (проверяется в JS-коде) — тогда фронтенд выполняет htmx-запрос к `/notifications/list/` для перерендера списка и показа всплывающего уведомления с текстом, зависящим от причины обновления.

#### Оптимизация SQL-запросов

Получение списка уведомлений (как в web-view, так и в api-view) оптимизировано через общий миксин `NotificationOptimizeMixin`. Он ограничивает выбираемые поля через `only()`, загружает пользователя-инициатора уведомления `actor` и тип связанного объекта `content_type` через `select_related`, а сам связанный объект `content_object` — через `GenericPrefetch`.

`GenericPrefetch` используется, поскольку из-за универсальности уведомлений поле `content_object` (`GenericForeignKey("content_type", "object_id")`) ссылается на связанный объект через пару полей `content_type` и `object_id`. `GenericPrefetch` работает по аналогии с `Prefetch`, только он группирует связанные объекты по их типам и предзагружает их отдельными SQL-запросами. При обычном `Prefetch` для одной связи выполняется один дополнительный SQL-запрос, а при `GenericPrefetch` число дополнительных SQL-запросов пропорционально числу уникальных типов связанных объектов (и их вложенным связям). Это позволяет предотвратить проблему `N+1` при использовании `GenericForeignKey` связи.

### 4.4 Роли пользователей, права и группы

<img width="1774" height="1244" alt="users" src="https://github.com/user-attachments/assets/3cba8d98-cb56-43d5-8d63-2067fa7f04f5" />

В Django-проекте реализованы роли пользователей с разными правами на основе поля `role` модели `User` в связке со стандартными группами и правами `permissions` Django, а также с кастомными правами моделей: `"block_user"` для `User`, `"moderate_post"` для `Post` и `"moderate_comment"` для `Comment`.

| Роль | Бейдж на фронтенде | Возможности |
|:---|:---|:---|
| `ADMIN` | Красный | Полный доступ к проекту за счет `is_superuser` |
| `MODERATOR` | Зелёный | Модерация контента (изменение и удаление чужих постов и комментариев) и блокировка пользователей |
| `STAFF_VIEWER` | Белый | Доступ только на чтение данных Django-админки без права редактирования |
| `USER` | Не отображается | Базовая роль по умолчанию, доступно создание контента |

#### Синхронизация роли с флагами и группами

Логика синхронизации роли `role` с флагами `is_superuser` и `is_staff` реализована в модели `User` и срабатывает автоматически при создании пользователя или при изменении поля `role`:

- **Флаги `is_staff` и `is_superuser`** — устанавливаются по словарю `ROLE_FLAGS_MAP`;
- **Группы (с набором прав)** — по словарю `ROLE_GROUPS_MAP`.

Словари заданы в модели `User` (Role — текстовый Choices-класс `models.TextChoices`):

```python
# Соответствие ролей пользователей и флагов "is_staff" и "is_superuser"
ROLE_FLAGS_MAP = {
    Role.ADMIN: {"is_staff": True, "is_superuser": True},
    Role.MODERATOR: {"is_staff": True, "is_superuser": False},
    Role.STAFF_VIEWER: {"is_staff": True, "is_superuser": False},
    Role.USER: {"is_staff": False, "is_superuser": False},
}
# Соответствие ролей пользователей и групп прав
ROLE_GROUPS_MAP = {
    # Role.ADMIN имеет все права, поскольку у него флаг is_superuser == True
    Role.MODERATOR: ["Moderators", "StaffViewers"],
    Role.STAFF_VIEWER: ["StaffViewers"],
}
```

Права, которые получают сами группы, определены отдельно в сервисном слое `users/services/permissions.py` в списках `MODERATOR_PERMISSIONS` и `STAFF_PERMISSIONS`, содержащих кортежи с парами (права) `(app_label, codename)`, где `app_label` — это название Django-приложения, а `codename` — это системное имя права.

#### Иерархия модерации

Возможность одного пользователя модерировать другого определяется приоритетом ролей `ADMIN` > `MODERATOR` > `STAFF_VIEWER` и `USER`, при этом `STAFF_VIEWER` и `USER` не могут модерировать. Приоритет задан через словарь в сервисной функции `can_moderate` в `users/services/permissions.py`. При этом запрещено модерировать самого себя, а также пользователей с равным или более высоким приоритетом — например, один модератор не может заблокировать другого модератора или администратора.

#### Блокировка пользователей

<img width="1715" height="968" alt="user-moderation" src="https://github.com/user-attachments/assets/93d12f14-7013-4949-b51f-282d9eae85e3" />

Блокировка и разблокировка вынесены в сервисный слой `users/services/moderation.py`. Перед изменением статуса проверяется право на модерацию через сервисную функцию `can_moderate`, после чего заполняются поля `is_blocked`, `blocked_at`, `blocked_by`.

Блокировка ограничивает доступ пользователя к аккаунту:
- вход по логину и паролю и уже открытая сессия при каждом запросе проверяются на уровне кастомных бекендов аутентификации Django (`users/authentication_backends.py`) — вдобавок к стандартному `is_active` проверяется также `is_blocked`;
- вход через OAuth для уже существующего заблокированного пользователя отклоняется в адаптере `django-allauth` (метод `pre_social_login`) с сообщением о блокировке и редиректом на главную страницу;
- для API-запросов кастомные классы аутентификации (для сессии, DRF-токена и JWT, классы переопределяются в `users/api/authentication.py`) не аутентифицируют заблокированного пользователя, возвращается `401-ый` ответ.

Ранее в проекте принудительный выход заблокированных пользователей (ранее аутентифицированных) для web-запросов выполнялся через `BlockedUserMiddleware`. С появлением кастомных бекендов аутентификации (проверяющих, помимо `is_active`, ещё и `is_blocked`) middleware перестал иметь надобность: заблокированный пользователь становится анонимным при первом обращении к объекту `request.user`. Когда срабатывает бекенд аутентификации (в БД для каждой сессии вместе с `user_id` сохраняется бекенд, нашедший пользователя ранее при его аутентификации через authenticate()), он не возвращает пользователя (при наличии сессии ищет через `backend.get_user(user_id)`), поэтому `request.user` становится анонимным (`AnonymousUser`) и `BlockedUserMiddleware` не имеет надобности, поскольку всегда работает с `AnonymousUser`. Middleware оставлен в проекте для истории разработки и защиты в случае изменения логики бекендов аутентификации.

### 4.5 Способы аутентификации, бекенды и классы аутентификации

### 4.5.1 Web

<div align="center">
  <img width="450" alt="login-page" src="https://github.com/user-attachments/assets/439b4780-dcc2-4303-aa60-852daa9a8107" />
</div>

Для web-части проекта (классические Django-views) используется классическая аутентификация Django через сессии (`django.contrib.sessions`) — после успешной аутентификации `user_id` и конкретный бекенд аутентификации, вернувший пользователя, сохраняются в сессии в БД (таблица `django_session`), а `sessionid` передаётся клиенту в cookie.

При дальнейших запросах от клиента сессия передается также через cookie. Стандартный `SessionMiddleware` читает `sessionid` из cookie, создает объект-сессию и сохраняет его в `request.session`. Затем стандартный `AuthenticationMiddleware` выполняет ленивую загрузку request.user `request.user = SimpleLazyObject(lambda: get_user(request))`. Запрос к БД для получения пользователя по его user_id будет отправлен только при обращении к каким-либо полям объекта `request.user`, который после этого будет закеширован в рамках выполнения запроса.

В проекте зарегистрировано два кастомных бекенда аутентификации (в `AUTHENTICATION_BACKENDS`), каждый расширяет свой стандартный класс и переопределяет метод `user_can_authenticate`, добавляя проверку `not user.is_blocked` к стандартной проверке поля `is_active`:

- **`CustomAuthenticationBackend`** (наследуется от `ModelBackend`) — используется при входе через логин и пароль при поиске пользователя для аутентификации или при наличии активной сессии;

- **`CustomAllAuthAuthenticationBackend`** (наследуется от allauth-бекенда `AuthenticationBackend`) — используется для поиска пользователей, аутентифицированных ранее через OAuth и имеющих активную сессию. Сам вход через соцсеть идёт в обход `authenticate()` (allauth логинит пользователя напрямую), но перед вызовом `login()` allauth проставляет пользователю путь именно к этому бекенду, поэтому все последующие запросы OAuth-пользователя используют `get_user()` именно от данного бекенда.

### 4.5.2 Api

<div align="center">
  <img width="500" alt="api-auth" src="https://github.com/user-attachments/assets/b085ed77-d7fc-410c-8d84-b46a85e14646" />
</div>

REST API поддерживает три независимых способа аутентификации, которые можно использовать одновременно:

- **Сессия** — тот же `sessionid`, что и в web-части;
- **DRF-токен** (`rest_framework.authtoken`) — при запросах передаётся в HTTP-заголовке `Authorization: Token <key>`, при аутентификации токен возвращается в теле ответа в JSON;
- **JWT-токены** (`djangorestframework-simplejwt` + `dj_rest_auth` для OAuth) — пара access и refresh JWT-токенов; при запросах access передаётся в HTTP-заголовке `Authorization: Bearer <token>`; для обновления access нужно передать refresh в теле запроса в JSON; при аутентификации токены возвращаются в теле ответа в JSON; при api-OAuth через `dj_rest_auth` токены возвращаются в HTTP-куках.

> Доступные api-эндпоинты можно посмотреть в документации OpenAPI через Swagger (открыта публично в демонстрационных целях) запущенного проекта.

Для каждого способа аутентификации нужно указать соответствующий класс в настройках DRF:

```python
REST_FRAMEWORK = {
    # ...
    # Поддерживаемые способы аутентификации
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.api.authentication.CustomTokenAuthentication",
        "users.api.authentication.CustomJWTAuthentication",
        "users.api.authentication.CustomSessionAuthentication",
    ],
    # ...
}

```

DRF при каждом запросе перебирает список классов из `DEFAULT_AUTHENTICATION_CLASSES` и вызывает `.authenticate(request)` у каждого по очереди, пока один не вернёт `(user, auth)` или не выбросит `AuthenticationFailed`. В отличие от бекендов Django, у DRF нет привязки конкретного класса аутентификации к токену.

Под каждый способ аутентификации в проекте написан свой класс аутентификации с проверкой блокировки пользователя (поля `is_blocked`) через общий миксин, классы прописаны в `users/api/authentication.py`:

- **`CustomSessionAuthentication`** (наследуется от `SessionAuthentication`) — стандартный родительский класс не содержит собственной логики получения пользователя, а читает уже готовый `request._request.user` — ленивый объект, подготовленный `AuthenticationMiddleware` через бекенды Django;

- **`CustomTokenAuthentication`** (наследуется от `TokenAuthentication`) — получает пользователя из БД по ключу токена (`Token.objects.get(key=key).user`);

- **`CustomJWTAuthentication`** (наследуется от `JWTAuthentication`) — получает пользователя из БД напрямую по `user_id` из payload access JWT-токена.

### 4.6 Аватары пользователей: генерация, хранение и использование

#### Общая логика системы аватаров пользователей

Для каждого пользователя задается несколько аватаров: оригинал и три миниатюры разного размера, которые хранятся в S3-хранилище и используются в разных элементах интерфейса на фронтенде у клиента. Миниатюры нужны, чтобы при отображении аватаров в уменьшенных размерах изображения корректно отображались (в уменьшенных окнах оригинал выглядел бы искаженным) и клиенту было проще загрузить легковесные изображения. Оригинальный аватар доступен для просмотра через клик ЛКМ по миниатюре (загружается в момент клика и кешируется браузером).

Генерация миниатюр вынесена в асинхронные `Celery-задачи`, поскольку обработка изображений через Pillow и их загрузка в S3-хранилище — это долгая операция. Реализация логики через асинхронные Celery-задачи позволяет пользователю не ждать создания миниатюр при загрузке нового аватара. Все `Celery-задачи` запускаются через `transaction.on_commit` — только после подтверждения транзакции БД.

Помимо генерации, реализованы валидация загружаемых файлов, подстановка стандартного аватара при отсутствии пользовательского, удаление устаревших файлов из S3 при смене или удалении аватара (сброс на стандартный) и очистка файлов пользователя при удалении аккаунта. Вся логика работы с аватарами вынесена в сервисный слой `users/services/` (`avatars.py`, `image_processing.py`, `validators.py`). Модель `User`, сигналы и Celery-задачи используют общий сервисный слой.

#### Обработка изображений в сервисном слое

Обработка изображений (статических и анимированных) осуществляется в сервисном слое `users/services/image_processing.py`, который работает с Pillow и возвращает готовое изображение в `BytesIO` — промежуточные файлы на диске не сохраняются. `BytesIO` позволяет работать с двоичными данными (байтами) в оперативной памяти как с файлом на жестком диске. Используется, поскольку Pillow умеет сохранять результат только "в файл".

#### Celery-задачи генерации и удаления аватаров

Все задачи при декорировании через `@shared_task` объявлены с параметрами:

- `ignore_result=True` — результаты задач не хранятся;
- `acks_late=True` — задача подтверждается только после выполнения;
- `reject_on_worker_lost=True` — при падении воркера задача возвращается в очередь брокера.

Celery-задачи для работы с аватарами идемпотентны, поэтому их можно перезапускать при падении Celery-воркера.

| Celery-задача | Что делает | Когда запускается |
|---|---|---|
| `generate_and_save_avatars_small` | Генерирует миниатюры всех размеров и сохраняет их пути в полях модели | При загрузке нового аватара пользователем |
| `download_and_set_avatar` | Скачивает аватар по URL провайдера (при OAuth), валидирует, сохраняет в хранилище и обновляет пользователя | При регистрации через OAuth |
| `delete_old_avatars_from_s3_storage` | Удаляет переданный список файлов; без списка сама сверяет содержимое "папки" пользователя в S3 с актуальными полями модели и удаляет лишние файлы | При загрузке нового аватара или при сбросе аватара на стандартный |
| `delete_all_avatars_files_task` | Удаляет все файлы из "папки" `avatars/<s3_storage_uuid>` | При удалении пользователя (вызывается обработчиком сигнала `post_delete` модели `User`) |

#### Пути хранения файлов в S3 хранилище

Файлы аватаров пользователя лежат в отдельной "папке" (префиксе ключа) вида `avatars/<s3_storage_uuid>/`, имя файлов генерируется из UUID (один для оригинала и миниатюр) с сохранением исходного расширения:

```plaintext
avatars/<s3_storage_uuid>/<file_uuid>.<ext>                 # оригинал
avatars/<s3_storage_uuid>/<file_uuid>_small_size1.<ext>     # миниатюра 100x100
avatars/<s3_storage_uuid>/<file_uuid>_small_size2.<ext>     # миниатюра 170x170
avatars/<s3_storage_uuid>/<file_uuid>_small_size3.<ext>     # миниатюра 800x800
```

Поле `s3_storage_uuid` — отдельный `UUIDField` модели `User`, задается один раз при создании пользователя и больше не меняется. В пути он используется вместо `pk` или `username` по причинам:

- при загрузке фикстур БД `pk` пользователей меняется, поэтому привязка уже загруженных файлов в S3-хранилище к пользователям была бы потеряна;
- при смене `username` пользователем пришлось бы копировать все файлы в S3 под новыми ключами и удалять старые (изменить ключ файла в S3 нельзя).

#### Логика обработки аватаров в модели `User`

Возможны три сценария:

**1) Создание пользователя**

Если аватар отличается от стандартного, запускается `Celery-задача` генерации миниатюр `generate_and_save_avatars_small`.

**2) Загрузка нового аватара**

Поля миниатюр задаются как `None`, и до окончания фоновой генерации миниатюр поля-свойства `avatar_small_*_url` отдают URL оригинала. После коммита запускается **цепочка (chain)** Celery-задач:

```python
# цепочка celery задач на создание миниатюр и удаление предыдущих
# .si - immutable signature - результат первой задачи не передается во вторую
tasks = chain(
    generate_and_save_avatars_small.si(self.pk),
    delete_old_avatars_from_s3_storage.si(self.pk, avatar_names_for_delete),
)

# Запуск задач только после завершения сохранения в БД
transaction.on_commit(lambda: tasks.apply_async())
```

Старые файлы удаляются только после того, как новые миниатюры успешно созданы.

**3) Сброс аватара на стандартный**

Если пользователь очистил поле аватара, `avatar` и все миниатюры возвращаются к значениям по умолчанию, после сохранения в БД изменений запускается только Celery-задача `delete_old_avatars_from_s3_storage` со списком файлов на удаление. Если предыдущий аватар был стандартным (удалять нечего), задача не запускается.

Сохранение миниатюр Celery-задача выполняет через `save(update_fields=[...])`, что вызывает сигнал `post_save` и инвалидацию кеша объекта пользователя через обработчик сигнала, поэтому новые URL миниатюр появляются в интерфейсе клиента сразу после их сохранения.

#### Использование аватаров пользователей

Для html-шаблонов и api-сериализаторов у модели заданы поля-свойства, отдающие url соответствующей миниатюры при ее наличии или же url оригинала:

```python
@property
def avatar_small_size1_url(self) -> str | None:
    """URL миниатюры аватара размера size1."""
    return self.get_avatar_small_url("size1")

@property
def avatar_small_size2_url(self) -> str | None:
    """URL миниатюры аватара размера size2."""
    return self.get_avatar_small_url("size2")

@property
def avatar_small_size3_url(self) -> str | None:
    """URL миниатюры аватара размера size3."""
    return self.get_avatar_small_url("size3")

def get_avatar_small_url(self, size: str = "size1") -> str | None:
    """
    Возвращает URL конкретной миниатюры или URL оригинала аватара.

    При загрузке нового аватара, пока новые миниатюры еще не сгенерированы Celery-задачей,
    поля-миниатюры принимают значения None (задается в методе _reset_small_avatars при его
    вызове с default=None), поэтому текущий метод в случае отсутствия миниатюры вернет оригинал.
    """
    fields = {
        "size1": self.avatar_small_size1,
        "size2": self.avatar_small_size2,
        "size3": self.avatar_small_size3,
    }

    target_field = fields.get(size)
    if target_field:
        return target_field.url

    return self.avatar.url if self.avatar else None
```

#### Стандартные аватары

Пока пользователь не загрузил свой аватар, по умолчанию для аватара и миниатюр заданы стандартные файлы (лежат в S3 заранее общие для всех). Для создания дефолтных аватаров нужно загрузить оригинал дефолтного аватара в S3 с именем `avatars/default_avatar.jpg`, а затем создать уменьшенные копии через classmethod модели:

```python
User.generate_default_avatar_different_sizes()
```

Метод обращается к сервисной функции, которая открывает `default_avatar.jpg` из хранилища и для каждого размера из `AVATAR_SMALL_SIZES` сохраняет уменьшенную копию под соответствующим именем (для имен миниатюр используются константы, определенные на уровне модели `User`).

#### Валидация загружаемого файла

Загружаемый аватар проверяется кастомным валидатором `AvatarFileValidator` (`users/services/validators.py`):

- размер файла — не более 10 Мб;
- MIME-тип **по содержимому** файла: разрешены `jpeg`, `png`, `gif`, `webp`, `x-icon`;
- минимальные размеры изображения — от 100x100 px;
- соотношение сторон — от 0.25 до 4.

### 4.7 GIN-индексы с расширением pg_trgm для постов

Для поиска постов, содержащих введенный текст (вхождения подстроки), используются GIN-индексы с расширением PostgreSQL `pg_trgm` для полей `Post.title`, `Post.search_content` и `LowercaseTag.name`. Они позволяют осуществлять быстрый регистронезависимый поиск по вхождению подстроки. В самом SQL-запросе используется оператор PostgreSQL `ILIKE '%...%'`, что реализуется через кастомный lookup `ilike_icontains`.

#### GIN-индекс и триграммы

**GIN** (Generalized Inverted Index) — тип индекса PostgreSQL, эффективный для поиска по составным значениям, где одному значению столбца соответствует множество ключей индекса (поиск по вхождению подстроки, массивы, JSONB и триграммы).

Расширение **pg_trgm** разбивает строку на триграммы — подряд идущие последовательности из трех символов (например, слово `django` раскладывается на `  d`, ` dj`, `dja`, `jan`, `ang`, `ngo`, `go `). GIN-индекс хранит эти триграммы как ключи и позволяет PostgreSQL находить совпадения по общим триграммам между индексируемым значением и поисковым запросом, вместо посимвольного сравнения каждой строки таблицы. Благодаря этому оператор `ILIKE '%...%'` не требует полного скана таблицы, а использует индекс при больших объемах данных (от десятков тысяч записей).

Для использования триграмм при поиске в искомом тексте (в запросе используется `ILIKE '%...%'`) должно быть минимум три символа, иначе индекс нельзя будет использовать (при `ILIKE '...%'` с двумя символами индекс был бы использован) и будет выполнен полный скан таблицы (Sequential Scan). При трех введенных символах создается одна триграмма для поиска. При четырех символах и более — большее число триграмм, каждая из которых должна найтись в целевой строке поиска с финальной проверкой, что введенный текст содержится в найденных после индекса записях.

#### Подключение расширения pg_trgm

Расширение `pg_trgm` подключается через отдельную миграцию:

```python
# posts/migrations/0018_add_trigramextension.py

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0017_alter_post_title'),
    ]

    operations = [
        TrigramExtension(),
    ]
```

#### Объявление индексов в моделях

Индексы объявлены как `GinIndex` с опклассом `gin_trgm_ops` в `Meta.indexes` соответствующих моделей (`posts/models.py`):

```python
class LowercaseTag(TagBase):
    # ...

    class Meta:
        # ...
        indexes = [
            GinIndex(
                fields=["name"],
                opclasses=["gin_trgm_ops"],
                name="tag_name_trgm",
            ),
        ]

    # ...


class Post(models.Model):
    # ...

    class Meta:
        # ...
        indexes = [
            # ...
            GinIndex(
                fields=["title"],
                opclasses=["gin_trgm_ops"],
                name="post_title_trgm",
            ),
            GinIndex(
                fields=["search_content"],
                opclasses=["gin_trgm_ops"],
                name="post_content_trgm",
            ),
        ]

   # ...
```

Поле `search_content` — очищенная от HTML-тегов и лишних пробельных символов версия поля `rendered_content` (сгенерированный HTML-код из Markdown-поля `content`), задается в методе `save()` при создании объекта или изменении поля `content`.

Опкласс (класс операторов) задает правила работы с данными при создании индексов и их связь с операторами БД, в данном случае — создание триграмм из текста и правила связки триграмм и операторов БД. Без опкласса GIN индекс создать нельзя, нужно явно указать или `gin_trgm_ops` для триграмм или `tsvector_ops` (для поля `SearchVectorField` типа `tsvector`) для полнотекстового поиска по отдельным словам (с учетом разных форм слов), но уже без поиска вхождения подстроки.

#### Кастомный lookup, использование индекса

Чтобы обращаться к индексу через Django ORM для регистронезависимого поиска в `posts/lookups.py` реализован кастомный lookup `ilike_icontains`, компилирующий фильтр в `ILIKE '%значение%'`:

```python
# В SQL-запросе: WHERE title ILIKE '%django%'
Post.objects.filter(title__ilike_icontains="django")
```

Lookup работает только при использовании в качестве БД PostgreSQL, поскольку только данная БД имеет оператор `ILIKE`. Стандартный Django lookup для регистронезависимого поиска `icontains` не подходит, потому что тогда в SQL-запросе будет использоваться `LIKE UPPER('%значение%')`, что для использования индексов требует создания индексов на UPPER-версии полей, иначе индексы не будут использованы.

В проекте при поиске постов, содержащих введенный текст, используется:

```python
# Поиск постов, в title, search_content или tags__name которых есть текст q
queryset = queryset.filter(
    Q(title__ilike_icontains=q)
    | Q(search_content__ilike_icontains=q)
    | Q(id__in=post_ids_by_tags)  # найдено через tags__name__ilike_icontains
)
```

### 4.8 Поддержка Markdown и LaTeX

<img width="1837" height="1299" alt="markdown-latex-2" src="https://github.com/user-attachments/assets/a52ae061-babd-4960-8837-40a5a35b21a7" />

Для создания постов и комментариев реализована поддержка синтаксиса Markdown с возможностью вставки математических формул через LaTeX-синтаксис (правила разметки и результат для пользователей описаны в html-шаблоне `posts/templates/posts/_markdown_rules.html`). На бекенде исходный текст рендерится в безопасный HTML один раз при сохранении или при изменении, результат кешируется в БД. На фронтенде реализован live-предпросмотр без обращений к серверу.

#### Рендеринг Markdown в HTML на бекенде

Преобразование Markdown в безопасный HTML выполняется сервисной функцией `render_markdown_safe` из `posts/services/text_processing.py`:

1) Библиотека **`markdown2`** переводит текст в HTML с набором расширений `extras`:

```python
rendered_html = markdown2.markdown(
    protected_text,   # предварительно подготовленный введенный пользователем текст
    extras=[          # перечисление расширений (блоки кода, CSS-классы для подсветки текста, таблицы и так далее)
        # ...
    ],
)
```

При рендеринге производится защита LaTeX-формул. Формулы задаются через явные HTML-теги, которые рендерятся на фронтенде через KaTeX. Поскольку `markdown2` может искажать содержимое этих блоков, перед рендерингом Markdown оба типа блоков вырезаются из текста и заменяются на уникальные плейсхолдеры. После рендеринга HTML-теги с формулами возвращаются на место в исходном виде.

2) Полученный HTML очищается через `bleach.Cleaner` с указанием разрешенных списков HTML-тегов, атрибутов и CSS-свойств (используется `CSSSanitizer`), защищая от XSS и других атак:

```python
cleaner = Cleaner(
    tags=allowed_tags,
    attributes=allowed_attrs,
    css_sanitizer=css_sanitizer,
    protocols=["http", "https", "mailto"],
    strip=True,
    filters=[
        lambda source: LinkifyFilter(
            source,
            # "nofollow" - защита от спама, сайт не ручается за ссылки от пользователей,
            # нужна только для информирования поисковых роботов
            # "target_blank" - заставляет браузер открывать ссылку в новой вкладке
            callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
            # Не создавать ссылки из URL внутри блоков кода
            skip_tags=["pre", "code"],
        )
    ],
)
```

#### Использование в моделях

Поле `content` моделей `Post` и `Comment` содержит исходный Markdown-текст, а `rendered_content` — безопасный HTML после рендера и очистки. Рендеринг выполняется в методе `save()` только при создании объекта или при изменении поля `content`. У `Post` дополнительно на основе `rendered_content` формируется поле `search_content` — очищенный от HTML-тегов текст для поиска постов, содержащих введенный текст (вхождения подстроки).

#### Реализация на фронтенде

При создании и редактировании поста реализован live-предпросмотр рендеринга Markdown без обращения к серверу — рендеринг выполняется в браузере пользователя. Используются следующие JS-библиотеки, подключаемые как внешние CDN-скрипты:

- **`markdown-it`** — рендеринг текста Markdown в HTML в браузере (аналог `markdown2` на бекенде);
- **`highlight.js`** — подсветка синтаксиса кода в блоках `<pre><code>`, используются дополнительные языковые пакеты (подключаются также как внешние CDN-скрипты);
- **`KaTeX`** — рендеринг математических формул LaTeX внутри блоков `<span class="math-inline"></span>` и `<div class="math"></div>`.

Для показа уже готовых постов и комментариев также используются `highlight.js` для подсветки синтаксиса кода и `KaTeX` для рендеринга математических формул.

### 4.9 Кеширование

Кеш Django настроен через `django-redis` (`CACHES` в `studyoverflow/settings/celery_channel_cache.py`). В тестах он заменяется на `LocMemCache`, а прямые обращения к Redis — на `fakeredis`. Логика кеширования вынесена в сервисные слои приложений.

| Что кешируется | TTL | Где используется |
|:---|:---|:---|
| Объект пользователя | 10 минут | Публичный профиль |
| Объект поста | 10 минут | Детальная страница поста |
| Список всех тегов | 30 минут | Web: страницы списка, создания и редактирования постов (`ContextTagMixin`). API: список тегов без параметра `search` |
| Первая страница списка пользователей | 2 секунды | Страница списка пользователей для web |
| Список ID пользователей онлайн (кеш множества Redis) | 5 секунд | Список пользователей, фильтр по онлайну |
| Карта сайта `sitemap.xml` | 12 часов | Маршрут `sitemap.xml` в `studyoverflow/urls.py` |

#### Инвалидация кеша

Кеш сбрасывается обработчиками Django-сигналов (`users/signals.py`, `posts/signals.py`) через сервисный слой. При `.update()` операциях сигналы (в частности изменения объекта) не вызываются, поэтому инвалидация кеша осуществляется не через обработчик сигнала, а сразу при `.update()` операции:

| Событие | Что сбрасывается |
|:---|:---|
| Сохранение или удаление пользователя | Кеш объекта пользователя |
| Изменение счетчиков пользователя через .update() | Кеш объекта пользователя |
| Сохранение пользователя | Кеш всех постов этого пользователя, поскольку некоторые данные автора кешируются вместе с постом, так как используется `select_related` для оптимизации SQL-запросов для постов |
| Изменение или удаление поста | Кеш этого поста |
| Создание или удаление лайка поста, счетчик через .update() | Кеш поста, чтобы показать актуальный счетчик лайков |
| Создание или удаление комментария, счетчик через .update() | Кеш поста, чтобы показать актуальный счетчик комментариев |
| Создание, изменение или удаление тега | Кеш списка тегов |
| Создание или удаление связи "тег-пост" | Кеш списка тегов, чтобы показывать актуальный счетчик числа постов для каждого тега |

Кеш `sitemap.xml` не сбрасывается: новые посты и пользователи попадают в карту сайта после истечения TTL, равного 12 часам.

### 4.10 Онлайн-статус пользователей через Redis

Онлайн-статус пользователей хранится напрямую в Redis (через `django_redis.get_redis_connection`), а не через `django.core.cache.cache`, чтобы использовать не только пары "ключ-значение", но и множества Redis `set`, а также пакетные команды `pipeline`. Статус каждого пользователя хранится во временном ключе с TTL, равным 120 секунд, а ID всех пользователей (для которых задаются ключи) дополнительно собираются в общее множество, чтобы получать список всех, кто онлайн, одной операцией. API кеша Django умеет работать только с ключом, который уже известен (`get`, `set`, `delete`), и не предоставляет операций над множествами: `sadd` — добавление во множество, `srem` — удаление из множества и `smembers` — возвращает все элементы множества, также API кеша Django не позволяет работать с `pipeline` — конвейером, позволяющим выполнять несколько операций в Redis за один запрос.

Логика работы:

- при каждом HTTP-запросе аутентифицированного пользователя `OnlineStatusMiddleware` вызывает сервисную функцию `set_user_online`, а WebSocket-heartbeat (см. [4.3 Система уведомлений](#43-система-уведомлений)) продлевает статус онлайн, пока открыта вкладка браузера;
- `set_user_online` в одной pipeline-транзакции создает ключ `online_user:<user_id>` с TTL 120 секунд и добавляет ID пользователя во множество;
- при выходе из аккаунта сигнал `user_logged_out` удаляет ключ и запись из множества;
- сервисная функция `get_online_user_ids` читает множество, проверяет наличие ключей одним pipeline-запросом и удаляет из множества устаревшие ID;
- периодическая Celery-задача `sync_online_users_to_db` (через Celery Beat) каждые 60 секунд записывает текущее время в поле `last_seen` в БД тех, кто сейчас онлайн.

## 5. CI/CD-пайплайны

### 5.1 Используемые CI/CD-пайплайны

CI/CD-пайплайны реализованы через **GitHub Actions**, файлы workflow лежат в директории `.github/workflows/`.

| Пайплайн | Файл | Условие срабатывания | Назначение |
|:---|:---|:---|:---|
| **CI** | `ci.yml` | push в `main` | black, isort, flake8, mypy и pytest на dev-образе Django-проекта |
| **CD Checks** | `cd-checks.yml` | pull request в `release/cd` | Сборка и проверка prod- и prod-lite-сборок: smoke- и E2E-тесты |
| **CD Publish and Deploy** | `cd-publish-deploy.yml` | push в `release/cd` (в том числе коммит слияния при pull request) | Публикация Docker-образов в GHCR и деплой на сервер |
| **CD Deploy** | `cd-deploy.yml` | Вызывается из CD Publish and Deploy | Деплой на production-сервер по SSH |
| **CD Tag Release** | `cd-tag-release.yml` | push git-тега вида `v1.0.0` | Установка тегов с версией образам и создание GitHub Release |

```plaintext
main ── push ──► CI (ci.yml)
  │
  └─ pull request в release/cd ──► CD Checks (cd-checks.yml)
                                        │ 
                                        │ push в release/cd (при PR)
                                        ▼
                         CD Publish and Deploy (cd-publish-deploy.yml)
                          ├─ сборка и push образов в GHCR
                          └─ CD Deploy (cd-deploy.yml) ──► деплой на prod-сервер

git-тег vX.Y.Z ──► CD Tag Release (cd-tag-release.yml)
                   ├─ образы в GHCR получают тег версии vX.Y.Z
                   └─ создается GitHub Release
```

Ветка `release/cd` защищена ruleset'ом GitHub (**Settings → Rules → Rulesets**), запрещающим прямые коммиты в обход pull request.

### 5.2 CI: проверка кода Django-проекта

Пайплайн `ci.yml` проверяет код через dev-образ Django-проекта при каждом push в `main`. Шаги:

1) сборка dev-образа (`target: dev-image`) с кешированием слоев;
2) запуск в контейнере `studyoverflow-tests` из `docker-compose.test.yml` (с `--env-file .env.test`) проверок `black`, `isort`, `flake8`, `mypy` и `pytest`;
3) остановка и удаление контейнеров и томов.

Используется `.env.test` из репозитория, поэтому CI не требует секретов GitHub.

### 5.3 CD Checks: проверка prod- и prod-lite-сборок

Пайплайн `cd-checks.yml` проверяет production-сборки при pull request (до того, как изменения попадут в ветку `release/cd`). Состоит из двух независимых джоб:

- `build-prod-and-test` — полная prod-сборка;
- `build-prod-lite-and-test` — облегченная prod-lite-сборка.

Шаги каждой джобы:

1) сборка образов с кешем слоев и загрузка в локальный Docker на VM;
2) запуск сборки с ожиданием healthchecks всех сервисов;
3) smoke-тесты;
4) E2E-тесты;
5) при падении — сохранение артефактов (логи упавших E2E-тестов), вывод статуса контейнеров и логов всех сервисов;
6) остановка и удаление контейнеров и томов.

Используется `.env.test` из репозитория, поэтому CI не требует секретов GitHub. В пайплайне используются дополнительные файлы для запуска сборок: `docker-compose.cd.yml` для prod-сборки и `docker-compose.cd-lite.yml` для prod-lite-сборки, использующие `.env.test` и фиксированное имя Docker-сети `studyoverflow_network` для подключения отдельного контейнера E2E-тестов с playwright к запущенной сборке через Nginx по адресу `http://nginx:80`.

### 5.4 CD Publish and Deploy: публикация образов и деплой

Пайплайн `cd-publish-deploy.yml` срабатывает при push в `release/cd`, то есть после слияния pull request, проверенного в CD Checks. Состоит из двух последовательных джоб.

**1) `publish-images` — публикация образов в GHCR.** Джоба авторизуется в GitHub Container Registry, собирает prod-образы и отправляет их в реестр по адресу `ghcr.io/<владелец_репозитория>/<имя_образа>:<тег>`.

Каждый образ получает два тега:

- `latest` — актуальная версия, ее скачивает сервер при деплое;
- `<sha коммита>` — неизменяемая ссылка на образы конкретного коммита. От нее в CD Tag Release создается тег версии.

**2) `deploy-prod` — деплой.** Запускается только после успешной публикации всех образов (`needs: publish-images`) и вызывает `cd-deploy.yml`.

#### Деплой на сервер (cd-deploy.yml)

Workflow вызывается из CD Publish and Deploy, а также может быть запущен вручную. Шаги:

1) по SCP на сервер в `/app/studyoverflow` копируются файлы `docker-compose.yml`, `docker-compose.prod.yml` и `docker-compose.prod-lite.yml`;
2) по SSH на сервере выбирается набор compose-файлов по переменной репозитория `DEPLOY_MODE` (`lite` — с `docker-compose.prod-lite.yml`, `full` — без него), затем выполняется скачивание новых версий образов, запуск контейнеров и удаление старых образов, у которых нет запущенных контейнеров.

На сервере заранее должен лежать файл `.env.prod` в директории `/app/studyoverflow/`, заполненный по шаблону `.env.example`. Также должны быть установлены Docker и Docker Compose.

### 5.5 CD Tag Release: релиз по git-тегу

Пайплайн `cd-tag-release.yml` срабатывает при push git-тега формата `vX.Y.Z` (например, `v1.0.0`) и публикует релиз. Образы не пересобираются — используются образы, уже опубликованные в CD Publish and Deploy. Шаги:

1) **Установка тегов с версией образам.** Командой `docker buildx imagetools create` для каждого из 6 образов создается тег версии (например, `v1.0.0`) на основе существующего образа с тегом `<sha коммита>` (используется коммит, для которого задан git-тег). Образы не скачиваются и не пересобираются, используется копирование существующих манифестов образов.
2) **Подготовка `.env.example.release`.** Из `.env.example` создается копия, где `IMAGE_TAG` задается равным версии релиза, а имена образов заменяются на образы из GHCR;
3) **Создание GitHub Release** с названием `Release <версия>`. К релизу прикрепляются файлы для запуска prod- и prod-lite-сборок.

### 5.6 GitHub переменные и секреты для CI/CD-пайплайнов

GitHub переменные и секреты задаются в репозитории: **Settings → Secrets and variables → Actions** (вкладки **Variables** и **Secrets**). Используются только для деплоя.

| Название | Тип | Где используется | Описание |
|:---|:---|:---|:---|
| `DEPLOY_MODE` | Variable | `cd-deploy.yml` | Режим prod-сборки на сервере: `lite` или `full` |
| `PROD_SSH_HOST` | Secret | `cd-deploy.yml` | Адрес production-сервера |
| `PROD_SSH_USER` | Secret | `cd-deploy.yml` | Пользователь для подключения по SSH |
| `PROD_SSH_PASSWORD` | Secret | `cd-deploy.yml` | Пароль пользователя для подключения по SSH |
| `GITHUB_TOKEN` | Создается GitHub автоматически | `cd-publish-deploy.yml`, `cd-tag-release.yml` | Вход в GHCR и создание релиза |

Файлы окружения в CI/CD-пайплайнах:

- `CI` и `CD Checks` используют `.env.test` из репозитория;
- для `CD Deploy` необходим `.env.prod` на сервере;
- `CD Tag Release` использует `.env.example` из репозитория как основу для `.env.example.release`.

## 6. Тестирование

### 6.1 Модульные и интеграционные тесты через pytest

Тесты Django-проекта находятся в пакетах `tests/` приложений `navigation`, `users`, `posts` и `notifications`, запускаются через **pytest** с плагином **pytest-django**. Тестируются:

- модели, формы, сериализаторы и сервисный слой;
- web-views и api-views вместе с миксинами;
- сигналы, Celery-задачи, WebSocket-консьюмеры, middleware;
- взаимодействие моделей — счетчики, уведомления и каскадные удаления (`navigation/tests/test_integrations.py`).

#### Плагины и библиотеки pytest

| Библиотека | Назначение |
|:---|:---|
| `pytest-django` | Интеграция с Django: тестовая БД, `client`, `@pytest.mark.django_db` и так далее |
| `pytest-mock` | Фикстура `mocker` для подмены объектов |
| `pytest-xdist` | Параллельный запуск тестов в нескольких процессах |
| `pytest-timeout` | Ограничение времени выполнения теста |
| `pytest-asyncio` | Асинхронные тесты (например, WebSocket-консьюмеров Django Channels) |
| `pytest-cov` | Расчет покрытия кода тестами |
| `factory_boy` (+ Faker) | Фабрики тестовых данных |
| `fakeredis` | Имитация сервера Redis в оперативной памяти |

#### Настройки pytest

Настройки заданы в `studyoverflow/pytest.ini`:

- `DJANGO_SETTINGS_MODULE = studyoverflow.settings.test` — настройки проекта для тестирования;
- `--reuse-db` — тестовая БД сохраняется между запусками. После появления новых миграций БД нужно пересоздать: `pytest --create-db --timeout=0`. Флаг `--timeout=0` обязателен, чтобы успели примениться миграции;
- `--timeout=10` — тест падает при заданном таймауте;
- `-n 4` — параллельный запуск в 4 процессах;
- `--strict-markers` — нельзя использовать незарегистрированные маркеры;
- `filterwarnings = error` — предупреждения (Warnings) заставляют тесты падать с ошибками.

#### Изоляция от внешних сервисов

Настройки для тестирования `studyoverflow/studyoverflow/settings/test.py` заменяют внешние сервисы локальными аналогами, для тестирования как отдельный сервис нужен только **PostgreSQL**:

| Компонент | В проекте | В тестах |
|:---|:---|:---|
| БД | PostgreSQL | Реальный PostgreSQL |
| Кеш | `django-redis` | `LocMemCache` |
| Channel Layer (WebSocket) | `channels_redis` | `InMemoryChannelLayer` |
| Медиа-файлы (аватарки) | S3 | `InMemoryStorage` |
| Celery | Брокер Redis | Eager-режим: `CELERY_TASK_ALWAYS_EAGER` — Celery-задачи выполняются сразу, `CELERY_TASK_EAGER_PROPAGATES` — при ошибке в задаче тест падает |
| Email | SMTP | `locmem`, письма проверяются через `mail.outbox` |
| Прямые обращения к Redis (онлайн-статус) | Redis | `fakeredis` |
| Хешер паролей | Стандартный Django | `MD5PasswordHasher` для ускорения тестов |

#### Фикстуры и фабрики

- `studyoverflow/factories.py` — фабрики Factory Boy: `UserFactory`, `PostFactory`, `CommentFactory`, `LikeFactory` и `NotificationPostCreateFactory`;
- `studyoverflow/conftest.py` — глобальные фикстуры: обертки над фабриками (`user_factory`, `post_factory` и другие), `api_client`, автоматическая подмена Redis на `fakeredis`, а также хелперы для проверки LoginRequired логики эндпоинтов и 404-ых ответов.

#### Покрытие кода

Конфигурация `studyoverflow/.coveragerc` включает branch coverage и исключает из расчета служебные файлы и папки. Запуск проверки покрытия кода тестами:

```bash
cd studyoverflow
pytest --cov=. --cov-report=term-missing
```

### 6.2 Сценарии запусков модульных и интеграционных тестов

| Место запуска | Способ запуска | Особенности |
|:---|:---|:---|
| **Локально на хосте** | `pytest` в каталоге `studyoverflow/` | Нужны `Python` с dev-зависимостями Django-проекта и `PostgreSQL` на хосте |
| **Локально через Docker** | `docker-compose.test.yml` | Используются `Docker-контейнеры` с dev-версией Django-проекта и PostgreSQL |
| **pre-commit** | Хук `django-tests` | Запускается при коммите, если в индексе есть Python-файлы из `studyoverflow/`, E2E-тесты игнорируются |
| **CI** | `pytest -p no:cacheprovider -c pytest.ini` | Запускаются при push в `main` вместе с `black`, `isort`, `flake8` и `mypy` |

#### Запуск на хосте без Docker

Нужны Python с dev-зависимостями из `requirements.dev.lock.txt` и PostgreSQL на хосте. Django-настройки всегда читают `.env.test` (см. [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения)): по умолчанию в нем заданы `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432` и тестовые данные для БД, чтобы можно было запускать тесты локально без поднятия Docker-контейнера с БД. При необходимости можно заменить их на свои — пользователь должен иметь право создавать базы данных, так как pytest-django создает отдельную тестовую БД. Команда запуска тестов на хосте без Docker:

```bash
cd studyoverflow
pytest
```

> Pytest нужно запускать из каталога `studyoverflow/`: там лежат `pytest.ini` (с `DJANGO_SETTINGS_MODULE`) и `.coveragerc`.

#### Запуск через Docker (аналогично в CI)

Тесты запускаются в контейнере из образа `dev-image` (target в `Dockerfile` с dev-зависимостями), код монтируется с хоста, сервис `postgres` поднимается автоматически. Переменные `POSTGRES_HOST` и `POSTGRES_PORT` переопределяются в самом `docker-compose.test.yml`, поэтому `.env.test` менять не нужно:

```bash
docker compose -p studyoverflow-test -f docker-compose.test.yml --env-file .env.test run --rm studyoverflow-tests
```

Удаление оставшихся после выполнения тестов контейнеров (с БД):

```bash
docker compose -p studyoverflow-test -f docker-compose.test.yml --env-file .env.test down
```

#### Запуск в pre-commit

Поскольку в проекте настроен `pre-commit` с хуком `django-tests`, для возможности коммитить изменения нужно в файле `.env.test` указать настройки БД либо для локальной БД на хосте, либо для БД в Docker-контейнере.

### 6.3 E2E-тесты через Playwright

E2E-тесты проверяют запущенную production-сборку с точки зрения пользователя: сценарии тестирования выполняются в реальном браузере (по умолчанию Chromium) через **Playwright** и **pytest** (`pytest-playwright`). E2E-тесты находятся в директории `e2e/` и выполняются независимо от Django-проекта — production-сборка проверяется через подключение по HTTP тестирующего playwright-контейнера к контейнеру с nginx production-сборки. Директория `e2e/` игнорируется Pytest в Django-проекте `studyoverflow` (в том числе в pre-commit), но форматтеры, линтеры и mypy в pre-commit проверяют `e2e/` тоже.

Сценарии для E2E-тестирования из директории `e2e/tests/`:

| Файл | Сценарий |
|:---|:---|
| `test_auth.py` | Регистрация → вход → смена пароля → выход → вход со старым паролем (ошибка) → вход с новым паролем → удаление аккаунта → вход после удаления (ошибка) |
| `test_profile.py` | Редактирование своего профиля; просмотр чужого профиля (нет кнопок редактирования и удаления) |
| `test_posts.py` | Создание поста → поиск поста → детальная страница → редактирование → удаление |
| `test_comments.py` | Дерево комментариев двух пользователей; создание, редактирование и удаление комментариев |
| `test_likes_notifications.py` | Лайк и снятие лайков для поста и комментария, проверка счетчика уведомлений |

Особенности реализации:

- **Page Object Model** — работа со страницами вынесена в классы `e2e/helpers/pages.py`;
- **независимые тесты** — каждый тест сам регистрирует пользователей через UI с уникальными данными (`e2e/helpers/data_generators.py`, фабрики в `e2e/tests/conftest.py`), поэтому тесты можно безопасно запускать параллельно (`-n 4`);
- **несколько пользователей одновременно** — для второго пользователя создается отдельный контекст браузера (`browser.new_context()`) с изолированными cookie и сессией;
- **внешние сервисы** (S3, SMTP, OAuth) в E2E-тестах не настраиваются, в `.env.test` для них заданы шаблонные значения. Поэтому связанные с ними сценарии в E2E-тестах не тестируются (логика, связанная с внешними сервисами, проверяется в модульных и интеграционных тестах Django-проекта).

#### Конфигурация E2E-тестов

- **Docker-образ** (`e2e/Dockerfile`) основан на официальном образе `mcr.microsoft.com/playwright/python` с установленными браузерами. Версия образа должна совпадать с версией `playwright` в `e2e/requirements.lock.txt`;
- **Адрес тестируемого проекта** задается переменной `BASE_URL=http://nginx:80` в `e2e/docker-compose.e2e.yml`, в тестах используются относительные пути (`page.goto("/")`). Хост `nginx` добавлен в `DJANGO_ALLOWED_HOSTS` в `.env.test`, чтобы Django не отклонял запросы от контейнера с Playwright;
- **Docker-сеть** — контейнер с Playwright подключается к внешней Docker-сети `studyoverflow_network` и обращается к Nginx по имени сервиса `nginx`. Тестируемая сборка должна быть запущена заранее с фиксированным именем сети;
- **Логи упавших тестов** — при падении теста сохраняется Playwright trace (`--tracing=retain-on-failure`) в `e2e/test-results/` в виде zip-архивов для каждого теста. Открыть архив можно на сайте [trace.playwright.dev](https://trace.playwright.dev/).

### 6.4 Запуск E2E-тестов

E2E-тесты запускаются для тестирования prod- или prod-lite-сборки, поднятой с дополнительным файлом конфигурации для CD (`docker-compose.cd.yml` или `docker-compose.cd-lite.yml`)).

1) Запустите нужную сборку, порт `80` на хосте должен быть свободен:

Полная prod-сборка:

```bash
docker compose -p studyoverflow-cd -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.cd.yml --env-file .env.test up -d --wait
```

Prod-lite-сборка:

```bash
docker compose -p studyoverflow-cd -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.prod-lite.yml -f docker-compose.cd-lite.yml --env-file .env.test up -d --wait
```

> Имя Docker-сети фиксированное для подключения отдельного контейнера E2E-тестов с playwright к запущенной сборке через Nginx, поэтому одновременно можно запускать только одну из сборок. После изменения кода приложения добавьте в команду флаг `--build`.

2) Запустите E2E-тесты (после прогона тестов контейнер удалится автоматически):

```bash
docker compose -p studyoverflow-e2e -f e2e/docker-compose.e2e.yml run --rm playwright
```

3) Остановите сборку и удалите контейнеры и тома (команда с теми же `-f` файлами, что и при запуске), например для prod-сборки:

```bash
docker compose -p studyoverflow-cd -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.cd.yml --env-file .env.test down -v
```

E2E-тесты прогоняются автоматически в пайплайне `cd-checks.yml`, запускаемом при pull request в ветку `release/cd`, где независимо проверяются и prod-сборка, и prod-lite-сборка. Подробнее в [5.3 CD Checks: проверка prod- и prod-lite-сборок](#53-cd-checks-проверка-prod--и-prod-lite-сборок).

## 7. Инструменты разработки

### 7.1 Pre-commit

[**Pre-commit**](https://pre-commit.com/) — инструмент, который автоматически запускает проверки кода при каждом `git commit`. Если одна из проверок (хуков) при коммите завершилась с ошибкой, коммит не создается.

Конфигурация хуков находится в файле `.pre-commit-config.yaml` в корне репозитория.

#### Используемые хуки

Все хуки объявлены как `repo: local` с `language: system`: pre-commit не скачивает и не устанавливает инструменты в отдельные виртуальные окружения, а использует виртуальное окружение при разработке из `studyoverflow/requirements.dev.lock.txt`, команды хуков запускаются в терминале, в котором была выполнена команда `git commit`. Настройки инструментов лежат в каталоге `studyoverflow/`.

| Хук | Инструмент | Файл настроек | Что проверяет |
|:---|:---|:---|:---|
| `black` | black | `studyoverflow/pyproject.toml` раздел `[tool.black]` | Форматтер: автоматическое форматирование кода |
| `isort` | isort | `studyoverflow/pyproject.toml` раздел `[tool.isort]` | Форматтер: автоматическая сортировка импортов |
| `flake8` | flake8 | `studyoverflow/.flake8` | Линтер: стиль кода, логические ошибки и цикломатическая сложность (for, if-else и другие ветвления) кода |
| `mypy` | mypy | `studyoverflow/pyproject.toml` раздел `[tool.mypy]` | Статическая проверка типов |
| `django-tests` | pytest | `studyoverflow/pytest.ini` | Модульные и интеграционные тесты Django-проекта |

Хуки `black`, `isort`, `flake8` и `mypy` проверяют и Django-проект `studyoverflow/`, и E2E-тесты `e2e/`. Хук `django-tests` запускает тесты только Django-проекта, директория `e2e/` игнорируется через `--ignore=e2e` — E2E-тесты запускаются отдельно (см. [6.3 E2E-тесты через Playwright](#63-e2e-тесты-через-playwright)).

#### Особенности работы хуков

- **Проверка только измененных файлов.** Хуки `black`, `isort`, `flake8` и `mypy` запускаются с `pass_filenames: true` — им передаются только Python-файлы, добавленные в индекс (подготовленные к коммиту).
- **Исключения.** Из проверок исключены служебные файлы и каталоги.
- **Автоисправление.** `black` и `isort` изменяют файлы. Если были внесены исправления, изменения нужно будет добавить в индекс (`git add`) и повторить коммит.
- **Запуск всех тестов.** Хук `django-tests` использует `pass_filenames: false`, поэтому pytest запускается для всего Django-проекта, а не только для измененных файлов. Подробнее в главе [6.1 Модульные и интеграционные тесты через pytest](#61-модульные-и-интеграционные-тесты-через-pytest).
- **Файлы тестов вне индекса.** Если файл `test_*.py` изменен, но не добавлен в индекс, pytest запустит его старую версию (из репозитория). Если файл не отслеживается Git (но не в .gitignore), то pytest его запустит.
- **Новые миграции.** После появления новых миграций тестовую БД нужно пересоздать вручную командой `pytest --create-db --timeout=0` из каталога `studyoverflow/`, иначе хук `django-tests` упадет из-за устаревшей структуры БД.
- **Окружение на хосте.** Все хуки используют `language: system`, что было описано выше, поэтому на хосте должен быть установлен Python с dev-зависимостями проекта `studyoverflow/requirements.dev.lock.txt`, а коммит нужно выполнять из активированного виртуального окружения.
- **База данных для тестов.** Поскольку тесты запускаются на хосте, в `.env.test` должны быть указаны настройки подключения к PostgreSQL на хосте или в Docker-контейнере, подробнее в [2.4 Настройка переменных окружения](#24-настройка-переменных-окружения) и [6.2 Сценарии запусков модульных и интеграционных тестов](#62-сценарии-запусков-модульных-и-интеграционных-тестов).

#### Установка и использование

1) Убедитесь, что установлены Python и dev-зависимости проекта из `studyoverflow/requirements.dev.lock.txt`. В активированном виртуальном окружении установите dev-зависимости (показан запуск команды из корня репозитория):

```bash
pip install -r studyoverflow/requirements.dev.lock.txt
```

2) Установите git-хук в локальный репозиторий:

```bash
pre-commit install
```

3) После этого проверки будут запускаться автоматически при каждом `git commit`.

Ручной запуск всех хуков для всех файлов проекта (не только для индекса):

```bash
pre-commit run --all-files
```

Запуск одного конкретного хука, например `flake8`:

```bash
pre-commit run flake8 --all-files
```

Пропуск хуков при коммите (не рекомендуется, проверки все равно выполнятся в CI при пуше коммита):

```bash
git commit --no-verify
```

### 7.2 Сборка и фиксация зависимостей через pip-tools

Зависимости Django-проекта и E2E-тестов управляются через [**pip-tools**](https://pip-tools.readthedocs.io/). Принцип работы: в файле `.in` вручную задаются **прямые** основные зависимости. Затем командой `pip-compile` собираются все требуемые внутренние зависимости для основных зависимостей из файла `.in` и создается полный список всех зависимостей с их точными версиями в lock-файле `.lock.txt`. Docker-образы и CI/CD-пайплайны устанавливают зависимости из lock-файлов, поэтому их версии всегда одинаковые.

#### Файлы зависимостей

| Файл `.in` — редактируется вручную | Lock-файл — генерируется командой | Что содержит | Где используется |
|:---|:---|:---|:---|
| `studyoverflow/requirements.base.in` | `studyoverflow/requirements.base.lock.txt` | Базовые (production) зависимости | В Docker-образах Django-проекта: `dev-image` и `prod-image` |
| `studyoverflow/requirements.dev.in` | `studyoverflow/requirements.dev.lock.txt` | Зависимости для разработки, включая базовые зависимости и дополнительные | Только в `dev-image` и в локальном окружении при разработке |
| `e2e/requirements.in` | `e2e/requirements.lock.txt` | Зависимости E2E-тестов | В Docker-образе с `playwright` |

В файле `requirements.dev.in` задано `-r requirements.base.in`, поэтому dev-зависимости включают в себя все базовые зависимости. Файл `requirements.dev.lock.txt` содержит **полный** набор зависимостей: базовые и дополнительные для разработки.

#### Генерация lock-файлов

Команды выполняются в активированном виртуальном окружении с dev-зависимостями проекта.

Для Django-проекта (команды `pip-compile` выполняются из каталога `studyoverflow/`):

```bash
cd studyoverflow
pip-compile requirements.base.in -o requirements.base.lock.txt
pip-compile requirements.dev.in -o requirements.dev.lock.txt
```

Для E2E-тестов (команда `pip-compile` выполняется из корня репозитория):

```bash
pip-compile e2e/requirements.in -o e2e/requirements.lock.txt
```

> Путь в команде влияет на служебный комментарий в начале lock-файла (`pip-compile --output-file=... ...`), поэтому команды нужно запускать из указанных каталогов, чтобы комментарии в файлах не менялись без причины и не вынуждали Docker пересобирать слои образов без нужды.

> Поскольку `requirements.dev.in` включает `requirements.base.in`, после изменения базовых зависимостей нужно пересоздавать **оба** lock-файла: и base, и dev.

#### Особенности зависимостей E2E-тестов

Версия `playwright` в `e2e/requirements.in` и `e2e/requirements.lock.txt` должна совпадать с версией базового образа `mcr.microsoft.com/playwright/python` в `e2e/Dockerfile`.

### 7.3 Docker-образы

В проекте используются кастомные Docker-образы, собираемые из соответствующих Dockerfile. Все кастомные образы, кроме `dev-версии Django-проекта` и `e2e-playwright`, публикуются в GHCR через `cd-publish-deploy.yml`.

#### Образы Django-проекта из `studyoverflow/Dockerfile`

Для Django-проекта используется multi-stage сборка из трех этапов: общий `base-image`, а также `dev-image` и `prod-image` поверх него:

- **`base-image`** — на базе `python:3.12-slim`, создание пользователя `userdj` и установка базовых зависимостей `requirements.base.lock.txt`;
- **`dev-image`** — на базе `base-image`, дополнительно устанавливаются dev-зависимости `requirements.dev.lock.txt` и копируется весь код проекта, не исключенный `.dockerignore`. Используется в dev-сборке и в тестах (CI и локальный запуск тестов);
- **`prod-image`** — на базе `base-image`, копируется только основной код Django-проекта (без тестов) с хоста. Используется в prod- и prod-lite-сборках.

Создаются два разных образа Django-проекта через `dev-image` и `prod-image` этапы multi-stage сборки: `studyoverflow-backend:dev` и `studyoverflow-backend:prod`. В GHCR публикуется только `prod-образ`.

В Docker Compose при описании сборки образа в секции `build` нужно указывать этап multi-stage сборки через `target`:

```yaml
build:
  context: ./studyoverflow
  dockerfile: Dockerfile
  # Указывается dev-image или prod-image
  target: prod-image
```

Команды сборки образов вручную:

```bash
docker build --target dev-image -t studyoverflow-backend:dev ./studyoverflow
docker build --target prod-image -t studyoverflow-backend:prod ./studyoverflow
```

#### Образы Nginx из `nginx/Dockerfile` и `nginx/Dockerfile-lite`

Prod и prod-lite образы Nginx устроены одинаково: базовый образ `nginx:latest`, внутрь копируются обе конфигурации (HTTP и HTTPS), а также shell-скрипт, который при старте контейнера выбирает нужный конфиг в зависимости от переменной окружения `NGINX_SSL_ENABLED` (подробнее в [3.1 Логика выбора HTTP- и HTTPS-конфигураций Nginx](#31-логика-выбора-http--и-https-конфигураций-nginx)). Один и тот же образ подходит для запуска по HTTP и HTTPS без пересборки.

#### Образы для мониторинга из `monitoring/`

Используются официальные образы `loki`, `promtail` и `grafana` с добавлением конфигов:

| Образ | Базовый образ | Добавляется |
|:---|:---|:---|
| `loki` | `grafana/loki:2.9.4` | `loki-config.yml` |
| `promtail` | `grafana/promtail:2.9.4` | `promtail-config.yml` |
| `grafana` | `grafana/grafana:13.1` | `datasource.yml` (автоподключение Loki как источника данных) |

#### Образ для E2E-тестов из `e2e/Dockerfile`

Используется базовый образ `mcr.microsoft.com/playwright/python:v1.61.0-jammy`, поверх которого устанавливаются зависимости и копируется код тестов. Образ не публикуется в GHCR.

Команда сборки образа вручную:

```bash
docker build -t e2e-playwright e2e/
```

### 7.4 Профилирование через pyinstrument

Для анализа производительности (времени выполнения запросов) в dev-сборке (`DEBUG=True`) используется профилирование через `pyinstrument`.

#### Pyinstrument — профилирование запроса

`Pyinstrument` — статистический (sampling) профайлер: вместо перехвата каждого вызова функции (как делают стандартные библиотеки `cProfile` и `profile`) он по умолчанию раз в 1 мс фиксирует текущий стек вызовов. `Pyinstrument` считает wall-clock время — полное физическое время, которое прошло с момента начала вызова функции до её завершения, таким образом видны ожидания I/O-bound задач, а не только процессорное время (что делает, например, `cProfile`).

Как профилировать конкретный запрос:

1) Убедиться, что сборка запущена с `DEBUG=True`.
2) Добавить `?profile` в конец URL нужной страницы, например `http://localhost:8000/posts/?profile`.
3) В качестве ответа вернётся HTML-страница с интерактивным деревом вызовов: сколько времени заняла каждая функция и её дочерние вызовы.

Профилирование запускается только при наличии `?profile` в URL.

> Профилирование через `pyinstrument` помогло обнаружить лишние обращения к S3-хранилищу при обновлении профиля пользователя — не был задан полный домен для S3 отдельным параметром, из-за чего при каждом обновлении профиля выполнялся дополнительный запрос к хранилищу.

Профилирование через `Django Debug Toolbar` не используется, поскольку оно использует `cProfile` и требует однопоточного режима в Python 3.12+ и некорректно отслеживает запросы с ASGI, для его использования нужно отключать `"daphne"` из `INSTALLED_APPS` при запуске Django-проекта через `python manage.py runserver 0.0.0.0:8000`. Поскольку используется `cProfile`, то будет показано только затраченное процессорное (CPU) время, время ожидания I/O-bound задач показано не будет, что также является причиной не использовать профилирование из `Django Debug Toolbar`.

### 7.5 Создание и применение фикстур — JSON-файлов с данными

В проекте используются Django-фикстуры — JSON-файлы с дампом данных БД, создаваемые командой `dumpdata` и загружаемые командой `loaddata`. Фикстуры используются для переноса демонстрационных данных из окружения локальной разработки в production-окружение.

#### Дамп и загрузка фикстур

Создание фикстуры:

```bash
python -Xutf8 manage.py dumpdata --natural-foreign --indent=2 -e contenttypes -e auth.Permission -e sessions -e admin -e authtoken -e token_blacklist -e socialaccount.SocialToken -e socialaccount.SocialApp -e account.EmailConfirmation -e sites -o db_prod_dump.json
```

Загрузка фикстуры:

```bash
python manage.py loaddata db_prod_dump.json
```

#### Параметры команды dumpdata

Используемые флаги:

- **`-Xutf8`** — флаг интерпретатора Python, включающий кодировку UTF-8 для всех операций ввода-вывода, игнорируя кодировку ОС, для корректного сохранения кириллицы;
- **`--natural-foreign`** — сохраняет внешние ключи `ForeignKey` не через `pk`, а через натуральный ключ `natural key` модели, например `username`. Например, вместо `content_type_id: 10` в дампе будет записано `["posts", "post"]` — натуральный ключ модели `ContentType`, а не ее `pk`;
- **`--indent=2`** — задает отступы в 2 пробела в итоговом JSON-файле;
- **`-e`** — исключает из дампа модели (указываются как приложения, так и модели), в том числе `ContentType` и `Permission`, которые создаются автоматически при миграциях и не должны переноситься между окружениями;
- **`-o`** — перенаправляет вывод команды в файл.

Не используется: **`--natural-primary`** — убирает `pk` из дампа для моделей, у которых определен натуральный ключ, чтобы не было конфликтов при загрузке в БД, где `pk` записей может отличаться. Флаг не используется, поскольку в моделях используются связи `GenericForeignKey`, для которых задается поле `object_id` как `PositiveIntegerField`, не имеющее связей, поэтому при дампе сохранятся числовые значения — `id` связанных объектов, и эти объекты должны иметь `pk` (`id`) в дампе.

Модели, которые исключаются из дампа флагами `-e` и не должны переноситься между окружениями:

| Приложение или модель | Таблица | Что описывает |
|:---|:---|:---|
| `contenttypes` | `django_content_type` | Метаданные моделей, создаются автоматически при `migrate` (сигнал `post_migrate`) |
| `auth.Permission` | `auth_permission` | Стандартные права доступа, создаются автоматически при `migrate` (сигнал `post_migrate`) |
| `sessions` | `django_session` | Сессии пользователей |
| `admin` | `django_admin_log` | История действий администраторов в Django админ-панели |
| `authtoken` | `authtoken_token` | DRF-токены аутентификации |
| `token_blacklist` | `token_blacklist_outstandingtoken`, `token_blacklist_blacklistedtoken` | Отозванные (заблокированные) refresh JWT-токены (`djangorestframework-simplejwt`) |
| `socialaccount.SocialToken` | `socialaccount_socialtoken` | Приватные access и refresh токены OAuth-провайдеров (Google, GitHub и других) (`django-allauth`) |
| `socialaccount.SocialApp` | `socialaccount_socialapp`, `socialaccount_socialapp_sites` | Client ID/Secret OAuth-провайдеров, которые заданы в БД, а не через переменные окружения (`django-allauth`) |
| `account.EmailConfirmation` | `account_emailconfirmation` | Одноразовые ключи подтверждения email со сроком действия (`django-allauth`) |
| `sites` | `django_site` | Системные настройки домена |

#### Обработка raw-фикстур в сигналах

Поскольку `loaddata` создает объекты моделей в обход обычной бизнес-логики, все обработчики сигналов `pre_save` и `post_save` в Django-проекте должны проверять флаг `raw` и прерывать выполнение при его наличии.

#### Перенос данных из одного окружения в другое при использовании Docker

При создании файла фикстуры на хосте напрямую из Docker-контейнера командой `docker exec <container> python -Xutf8 manage.py dumpdata <command flags> > db_prod_dump.json` сбивается кодировка `UTF-8`, поэтому кириллица в фикстуре отобразится некорректно. Флаг `-Xutf8` заставляет сам Python внутри контейнера писать в `stdout` в кодировке `UTF-8`, поток вывода передаётся на хост в неизменном виде (байт в байт), но, если оболочка хоста при записи через `>` интерпретирует эти байты в своей системной кодировке (на Windows), при записи в файл произойдет некорректная перекодировка. Поэтому нужно либо переключить кодировку консоли на `UTF-8` перед командой, либо создавать фикстуру в контейнере, а затем копировать файл на хост.

Инструкция создания и применения фикстуры при использовании Docker через создание файла внутри контейнера:

1) Зайти в контейнер от имени root (флаг `-u 0` / `--user 0`), чтобы иметь права на создание файла:

```bash
docker exec -it -u 0 <container> bash
```

2) Внутри контейнера создать фикстуру:

```bash
python -Xutf8 manage.py dumpdata --natural-foreign --indent=2 -e contenttypes -e auth.Permission -e sessions -e admin -e authtoken -e token_blacklist -e socialaccount.SocialToken -e socialaccount.SocialApp -e account.EmailConfirmation -e sites -o db_prod_dump.json
```

3) Скопировать фикстуру из контейнера на хост (команда выполняется на хосте):

```bash
docker cp <container>:/app/studyoverflow/db_prod_dump.json ./db_prod_dump.json
```

4) Скопировать фикстуру с хоста в целевой контейнер (например, другого окружения):

```bash
docker cp ./db_prod_dump.json <container>:/app/studyoverflow/db_prod_dump.json
```

5) Применить фикстуру внутри целевого контейнера:

```bash
docker exec <container> python manage.py loaddata db_prod_dump.json
```
