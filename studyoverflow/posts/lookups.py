from django.db.models import Lookup


class IContainsILike(Lookup):
    """
    Кастомный лукап (Lookup) для Django ORM, реализующий оператор ILIKE в PostgreSQL.

    Позволяет выполнять регистронезависимый поиск по подстроке через синтаксис:
    field__ilike_icontains="значение".
    Применяется для использования GIN + trigram индексов (pg_trgm) в PostgreSQL
    вместе с ILIKE по маске "%...%".
    """

    lookup_name = "ilike_icontains"  # кастомный lookup для фильтрации field__ilike_icontains

    def as_sql(self, compiler, connection):
        """
        Компилирует синтаксис Django ORM в сырой SQL-запрос для базы данных.

        :param compiler: Объект SQLCompiler, отвечающий за сборку и генерацию SQL.
        :param connection: Текущее подключение к базе данных.
        :return: (sql_string, list_of_params) - передача в драйвер БД.
        """
        # lhs = Left Hand Side - имя поля в базе в таблице, например "posts_post"."title"
        lhs, lhs_params = compiler.compile(self.lhs)
        # rhs = Right Hand Side - искомое значение
        rhs, rhs_params = self.process_rhs(compiler, connection)

        if rhs_params:
            rhs_params[0] = f"%{rhs_params[0]}%"

        # SQL-синтаксис для PostgreSQL
        return f"{lhs} ILIKE {rhs}", lhs_params + rhs_params
