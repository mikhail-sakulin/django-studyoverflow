REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "navigation.api.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "navigation.api.pagination.CustomPageNumberPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
}
