/*
    JS-скрипт для управления комментариями:
    - Показ/скрытие формы комментария (root)
    - Показ/скрытие формы ответа (reply)
    - Показ/скрытие формы редактирования (edit)
    - Делегирование событий клика для кнопок управления комментариями
    - Обработка кастомных событий HTMX для успешной отправки/ошибок форм
    - Перезагрузка страницы по кастомному событию
    - Скролл к комментарию по хэшу (#comment-card-{id}) после HTMX обновления
*/


document.addEventListener("DOMContentLoaded", function() {
    // --- Подсветка всех блоков <pre><code> ---
    function highlightCodeBlocks() {
        if (window.hljs) {
            hljs.highlightAll();
        }
    }
    // Подсветка при полной загрузке страницы
    highlightCodeBlocks();

    // Показ формы и блокировка кнопки
    function showForm(containerId, toggleBtn) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.style.display = "block";
        if (toggleBtn) toggleBtn.disabled = true;
    }

    // Скрытие формы и разблокировка кнопки
    function hideForm(containerId, toggleBtn) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.style.display = "none";
        if (toggleBtn) toggleBtn.disabled = false;
    }

    // --- Общая функция: ошибка редактирования комментария ---
    function activateEditErrorState(commentId) {
        const editContainer = document.getElementById(`edit-form-${commentId}`);
        const editBtn = document.querySelector(`.edit-comment-btn[data-comment-id="${commentId}"]`);

        if (editContainer) editContainer.style.display = "block";
        if (editBtn) editBtn.disabled = true;
    }

    // --- Делегирование кликов по всему телу документа ---
    document.body.addEventListener("click", function(event) {
        const target = event.target;

        // Root форма: показать
        if (target.id === "show-comment-form") {
            showForm("comment-form-container", target);
            return;
        }

        // Root форма: скрыть
        if (target.id === "cancel-comment") {
            hideForm("comment-form-container", document.getElementById("show-comment-form"));
            return;
        }

        // Reply форма: показать
        const replyBtn = target.closest(".reply-btn");
        if (replyBtn) {
            const commentId = replyBtn.dataset.commentId.trim();
            showForm(`reply-form-${commentId}`, replyBtn);
            return;
        }

        // Reply форма: скрыть
        const cancelReplyBtn = target.closest(".cancel-reply-btn");
        if (cancelReplyBtn) {
            const commentId = cancelReplyBtn.dataset.commentId.trim();
            hideForm(`reply-form-${commentId}`, document.querySelector(`.reply-btn[data-comment-id="${commentId}"]`));
            return;
        }

        // Edit форма: показать
        const editBtn = target.closest(".edit-comment-btn");
        if (editBtn) {
            const commentId = editBtn.dataset.commentId.trim();
            const editContainer = document.getElementById(`edit-form-${commentId}`);
            if (!editContainer) return;
            editContainer.style.display = "block";
            editBtn.disabled = true;
            return;
        }

        // Edit форма: скрыть
        const cancelEditBtn = target.closest(".cancel-edit-btn");
        if (cancelEditBtn) {
            const commentId = cancelEditBtn.dataset.commentId.trim();
            const editContainer = document.getElementById(`edit-form-${commentId}`);
            if (!editContainer) return;
            editContainer.style.display = "none";
            const editBtn = document.querySelector(`.edit-comment-btn[data-comment-id="${commentId}"]`);
            if (editBtn) editBtn.disabled = false;
            return;
        }
    });

    // --- HTMX события ---
    document.body.addEventListener("htmx:afterSwap", function(event) {
        const swappedEl = event.target;

        // --- Подсветка кода после каждого HTMX swap ---
        highlightCodeBlocks();

        // Если обновилась root форма, оставить её открытой
        if (swappedEl.id === "comment-form-container") {
            showForm("comment-form-container", document.getElementById("show-comment-form"));
        }

         // --- Кастомное событие ошибки при обновлении комментария (после HTMX swap) ---
        const triggers = event.detail.xhr?.getResponseHeader("HX-Trigger");
        if (!triggers) return;

        let parsed;
        try { parsed = JSON.parse(triggers); } catch { return; }

        if (parsed.commentUpdateError) {
            const commentId = parsed.commentUpdateError.commentId;
            activateEditErrorState(commentId);
        }
    });

    // --- Кастомные события root формы ---
    document.body.addEventListener("commentRootFormSuccess", function() {
        hideForm("comment-form-container", document.getElementById("show-comment-form"));
    });

    document.body.addEventListener("commentRootFormError", function() {
        showForm("comment-form-container", document.getElementById("show-comment-form"));
    });

    // --- Кастомные события reply формы ---
    document.body.addEventListener("commentChildFormSuccess", function(event) {
        const commentId = event.detail?.commentId;
        if (!commentId) return;
        hideForm(`reply-form-${commentId}`, document.querySelector(`.reply-btn[data-comment-id="${commentId}"]`));
    });

    document.body.addEventListener("commentChildFormError", function(event) {
        const commentId = event.detail?.commentId;
        if (!commentId) return;
        showForm(`reply-form-${commentId}`, document.querySelector(`.reply-btn[data-comment-id="${commentId}"]`));
    });

    // --- Кастомное событие перезагрузки страницы ---
    document.body.addEventListener('reloadPage', function() {
        window.location.reload();
    });

    // --- Кастомное событие ошибки при редактировании комментария ---
    document.body.addEventListener("commentUpdateError", function(event) {
        const commentId = event.detail?.commentId;
        if (!commentId) return;
        activateEditErrorState(commentId);
    });

    // --- Управление сортировкой комментариев ---
    document.body.addEventListener('click', event => {
        const btn = event.target.closest('.comment-sort-btn, .order-comment-btn');
        if (!btn) return;

        const isSort = btn.classList.contains('comment-sort-btn');
        const input = document.getElementById(isSort ? 'comment_sort_input' : 'comment_order_input');

        if (!input) return;

        // Если кнопка активна — снимается активность и сбрасывается input
        if (btn.classList.contains('active')) {
            btn.classList.remove('active');
            input.value = '';
        } else {
            // Деактивация всех кнопок этой группы
            const groupClass = isSort ? '.comment-sort-btn' : '.order-comment-btn';
            btn.closest('form').querySelectorAll(groupClass).forEach(b => b.classList.remove('active'));

            // Активация текущей кнопки
            btn.classList.add('active');
            input.value = btn.dataset.value;
        }
    });
});


// --- Скролл к комментарию по хэшу после HTMX обновления ---

// Если в URL есть хэш вида #comment-card-{id}, страница прокручивается к этому комментарию после загрузки
let scrolledToAnchor = false;

document.addEventListener("DOMContentLoaded", () => {
    const commentsWrapper = document.getElementById("comments-wrapper");
    if (!commentsWrapper) return;

    commentsWrapper.addEventListener("htmx:afterSwap", function(event) {
        if (scrolledToAnchor) return;

        const hash = window.location.hash;
        if (!hash) return;

        const el = document.querySelector(hash);
        // Проверка, что элемент является комментарием
        if (el && el.id.startsWith("comment-card-")) {
            // Плавная прокрутка к комментарию
            el.scrollIntoView({ behavior: "smooth", block: "start" });
            scrolledToAnchor = true;
        }
    });
});
