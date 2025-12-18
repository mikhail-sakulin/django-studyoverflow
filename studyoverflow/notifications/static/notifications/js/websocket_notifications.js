/*
    JS-скрипт для уведомлений через WebSocket:
    - Подключение к WS для получения количества непрочитанных уведомлений
    - Обновление счетчика уведомлений
    - Показ/скрытие иконки колокольчика и цвета
    - Анимация частиц при новых уведомлениях
    - Обновление списка уведомлений через HTMX
    - Автоматическое переподключение при обрыве соединения
    - Heartbeat: периодическое оповещение сервера, что пользователь онлайн
*/


document.addEventListener("DOMContentLoaded", function () {
    // Элементы уведомлений
    const buttonEl = document.getElementById("notifications-button");
    const iconEl = document.getElementById("i-notifications");
    const countEl = document.getElementById("notifications-count");
    const notificationsListEl = document.getElementById("notifications-list");

    if (!buttonEl || !iconEl || !countEl) return;
    if (window.notificationsWSInitialized) return;
    window.notificationsWSInitialized = true;

    // WS URL
    const wsScheme = location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsScheme}://${location.host}/ws/notifications/`;

    let socket;

    // --------------------------
    // Анимация новых уведомлений
    // --------------------------
    function animateNotification() {
        // Пульс иконки
        iconEl.classList.add("pulse");
        setTimeout(() => iconEl.classList.remove("pulse"), 500);

        // Частицы
        const container = buttonEl.querySelector(".notification-particles");
        for (let i = 0; i < 8; i++) {
            const particle = document.createElement("div");
            particle.classList.add("particle");

            // Случайное направление
            const angle = Math.random() * 2 * Math.PI;
            const radius = 20 + Math.random() * 10;
            particle.style.setProperty("--dx", `${Math.cos(angle) * radius}px`);
            particle.style.setProperty("--dy", `${Math.sin(angle) * radius}px`);

            container.appendChild(particle);
            setTimeout(() => particle.remove(), 600);
        }
    }

    // --------------------------
    // Подключение WebSocket
    // --------------------------
    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("WS connected");

            // --------------------------
            // Heartbeat: каждые 4 минуты сообщается серверу, что пользователь онлайн
            // --------------------------
            setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    // type "heartbeat" будет обрабатываться сервером
                    socket.send(JSON.stringify({ type: "heartbeat" }));
                }
            }, 60 * 1000); // 1 минута
        };

        socket.onmessage = event => {
            try {
                const data = JSON.parse(event.data);
                const count = data.unread_notifications_count ?? 0;
                const previousCount = parseInt(countEl.textContent) || 0;

                // Обновление счетчика
                countEl.textContent = count;

                // Смена иконки и цвета
                if (count > 0) {
                    iconEl.classList.remove("bi-bell");
                    iconEl.classList.add("bi-bell-fill");
                    countEl.classList.remove("text-warning");
                    countEl.classList.add("text-danger");

                    if (count > previousCount) animateNotification();
                } else {
                    iconEl.classList.remove("bi-bell-fill");
                    iconEl.classList.add("bi-bell");
                    countEl.classList.remove("text-danger");
                    countEl.classList.add("text-warning");
                }

                // --------------------------
                // Обновление списка уведомлений
                // --------------------------

                // Если сервер прислал флаг обновления списка
                if (data.update_list && notificationsListEl) {
                    // htmx запрос для обновления списка уведомлений
                    htmx.ajax('GET', '/notifications/list/', { target: '#notifications-list', swap: 'innerHTML' });
                }

            } catch (e) {
                console.error("WS parse error:", e);
            }
        };

        // --------------------------
        // Обработка закрытия WS
        // --------------------------
        socket.onclose = event => {
            if (!event.wasClean) {
                console.warn("WS disconnected, reconnecting...");
                setTimeout(connect, 5000);
            } else {
                console.log("WS closed cleanly");
            }
        };

        // --------------------------
        // Обработка ошибок WS
        // --------------------------
        socket.onerror = err => {
            console.error("WS error:", err);
            socket.close();
        };
    }

    // запуск WS
    connect();
});
