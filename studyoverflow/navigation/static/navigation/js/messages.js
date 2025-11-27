/*
    Скрипт для отображения сообщений Django (messages).
*/


document.addEventListener('DOMContentLoaded', () => {

    // Контейнер для сообщений с id="messages-container"
    const container = document.getElementById('messages-container');

    // Header страницы с id="header", под которым будут отображаться сообщения
    const header = document.getElementById('header');

    // Если контейнера нет, выполнение прекращается
    if (!container) return;

    // Функция позиционирования контейнера сообщения под header
    const positionMessages = () => {
        if (container) {
            if (header) {
                container.style.top = `calc(${header.offsetHeight}px + 2rem)`;
            } else {
                container.style.top = '2rem';
            }
        }
    };

    // Начальное позиционирование
    positionMessages();

    // Обновление позиционирования при изменении размера окна
    window.addEventListener('resize', positionMessages);

    // Автозакрытие всех сообщений через 3 секунды
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => {
            const alert = bootstrap.Alert.getOrCreateInstance(el);
            alert.close();
        });
    }, 3000);
});
