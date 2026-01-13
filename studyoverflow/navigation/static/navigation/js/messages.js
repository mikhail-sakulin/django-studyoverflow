/*
    Скрипт для отображения сообщений Django (messages).
*/


/* Функция позиционирования */
const positionMessages = () => {
    const container = document.getElementById('messages-container');
    const header = document.getElementById('header');
    if (!container) return;

    let topOffset = 32;
    if (header) {
        const rect = header.getBoundingClientRect();
        // Если хедер фиксированный или виден, отступ от его низа
        topOffset = Math.max(0, rect.bottom) + 32;
    }
    container.style.top = `${topOffset}px`;
};

/* Настройка при загрузке страницы */
document.addEventListener('DOMContentLoaded', () => {
    positionMessages();
    window.addEventListener('resize', positionMessages);
    window.addEventListener('scroll', positionMessages);

    // Закрытие сообщений, которые уже были в HTML
    document.querySelectorAll('#messages-container .alert').forEach(el => {
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(el);
            if (alert) alert.close();
        }, 3000);
    });
});

/* Обработка динамических сообщений */
document.body.addEventListener("showMessage", (event) => {
    const container = document.getElementById("messages-container");
    if (!container) return;

    const { text, type } = event.detail;

    const div = document.createElement("div");
    // Используется type или 'info' по умолчанию
    div.className = `alert alert-${type || 'info'} alert-dismissible fade show shadow mx-auto pe-auto`;
    div.role = "alert";
    div.style.pointerEvents = "auto";
    div.innerHTML = `
        ${text}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    container.appendChild(div);

    positionMessages();

    // Автозакрытие
    setTimeout(() => {
        if (typeof bootstrap !== 'undefined') {
            const alert = bootstrap.Alert.getOrCreateInstance(div);
            if (alert) alert.close();
        } else {
            div.remove();
        }
    }, 3000);
});
