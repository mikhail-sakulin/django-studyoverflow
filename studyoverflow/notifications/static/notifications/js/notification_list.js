/*
    JS-скрипт для управления уведомлениями:
    - Обработка кнопки "Отметить одно уведомление прочитанным"
    - Обработка кнопки "Отметить все уведомления прочитанными"
    - Показ/скрытие текста "Нет уведомлений"
    - Активация/деактивация кнопок после HTMX запросов
*/


(function () {
    function initNotificationHandlers() {

        // Контейнер со списком уведомлений
        const container = document.getElementById("notifications-list");

        // Контейнер с текстом "Нет уведомлений"
        const container_no_notifications = document.getElementById("container-no-notifications");

        // --------------------------
        // 1) Логика "Отметить прочитанным"
        // --------------------------
        document.body.addEventListener("htmx:afterRequest", function (event) {
            const trigger = event.detail?.elt;
            if (!trigger) return;

            // --- Одно уведомление ---
            if (trigger.classList.contains("mark-read-btn")) {
                const id = trigger.dataset.notificationId;
                const card = document.querySelector("#notification-card-" + id);
                if (card) card.classList.remove("border", "border-warning");

                trigger.classList.add("disabled");
                trigger.textContent = "Прочитано";
                return;
            }

            // --- Все уведомления ---
            if (trigger.id === "mark-all-read-btn") {

                // убрать подсветку со всех карточек
                document.querySelectorAll("[id^='notification-card-']").forEach((card) => {
                    card.classList.remove("border", "border-warning");
                });

                // обновить все кнопки "Прочитано"
                document.querySelectorAll(".mark-read-btn").forEach((btn) => {
                    btn.classList.add("disabled");
                    btn.textContent = "Прочитано";
                    btn.removeAttribute("hx-post");
                    btn.removeAttribute("hx-trigger");
                });
                return;
            }
        });

        // --------------------------
        // 2) Проверка количества уведомлений после HTMX swap
        // --------------------------
        document.body.addEventListener("htmx:afterRequest", function () {
            if (!container) return;

            const wrappers = container.querySelectorAll("[id^='notification-wrapper-']");
            const markAllBtn = document.getElementById("mark-all-read-btn");
            // кнопка "Удалить все оповещения"
            const deleteAllBtn = document.querySelector(".btn-outline-light.px-3");

            if (wrappers.length === 0) {
                if (container_no_notifications) {
                    // показать надпись
                    container_no_notifications.style.display = 'block';
                }
                // Сделать кнопки неактивными
                if (markAllBtn) markAllBtn.disabled = true;
                if (deleteAllBtn) deleteAllBtn.disabled = true;
            } else {
                if (container_no_notifications) {
                    // скрыть надпись
                    container_no_notifications.style.display = 'none';
                }
                // Сделать кнопки активными
                if (markAllBtn) markAllBtn.disabled = false;
                if (deleteAllBtn) deleteAllBtn.disabled = false;
            }
        });
    }

    // --------------------------
    // Инициализация
    // --------------------------
    if (window.htmx) {
        initNotificationHandlers();
    } else {
        document.addEventListener("htmx:load", initNotificationHandlers);
    }
})();
