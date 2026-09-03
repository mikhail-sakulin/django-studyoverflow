# Дата-миграция для генерации значений поля s3_storage_uuid модели User (уникальных UUID «папок» аватаров S3)
# для записей, у которых установлено значение поля как NULL, для уже существующих в БД пользователей.

import uuid

from django.db import migrations


# Вызывается при запуске команды migrate
def gen_uuid(apps, schema_editor):
    # Модель User из приложения users, какой она была зафиксирована на предыдущей миграции
    User = apps.get_model("users", "User")

    for user in User.objects.filter(s3_storage_uuid__isnull=True):
        user.s3_storage_uuid = uuid.uuid4()
        user.save(update_fields=["s3_storage_uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_user_s3_storage_uuid'),
    ]

    # reverse_code - определяет, что делать при откате миграции,
    # RunPython.noop - задает отсутствие операций при откате транзакции
    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop),
    ]
