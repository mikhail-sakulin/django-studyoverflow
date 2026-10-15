from rest_framework import serializers


class DetailSerializer(serializers.Serializer):
    """Сериализатор для ответов с полем "detail", используемый в схемах OpenAPI."""

    detail = serializers.CharField()
