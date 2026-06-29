FROM python:3.12-slim

# Создается группа пользователей
# -r (--system) - создание системной группы
# Создается новый пользователь и добавляется в созданную группу
# -r (--system) - создание системного пользователя (не создается домашняя директория)
# -g - задает основную группу для пользователя
RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

# Запрещает Python создавать .pyc файлы
ENV PYTHONDONTWRITEBYTECODE=1
# Выключает буферизацию stdout/stderr - логи сразу идут в Docker logs
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

# Остальные команды выполняются относительно /app/studyoverflow (рабочая директория)
WORKDIR /app/studyoverflow

COPY requirements.txt .

# --no-cache-dir - не сохранять pip cache для уменьшения веса образа
RUN pip install --no-cache-dir -r requirements.txt

COPY new_requirements.txt .
RUN pip install --no-cache-dir -r new_requirements.txt

COPY . .

# Создаются директории celerybeat_data и staticfiles
# -p - создает промежуточные папки, если их нет
RUN mkdir -p /app/studyoverflow/celerybeat_data /app/studyoverflow/staticfiles

# Смена владельца созданных директорий с root на пользователя userdj
# -R - рекурсивно (включая вложенные файлы)
RUN chown -R userdj:groupdjango /app/studyoverflow/celerybeat_data /app/studyoverflow/staticfiles

# Переключение на пользователя userdj в целях безопасности
USER userdj
