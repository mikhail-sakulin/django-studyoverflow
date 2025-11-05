/*
    JS-скрипт для:
    - отображения и скрытия формы добавления комментария,
    - обработки кнопок "Отмена" для закрытия форм
*/


// Ожидание полной загрузки DOM-дерева
document.addEventListener("DOMContentLoaded", function() {

    // Получение ссылок на основные элементы управления формой комментария
    const showBtn = document.getElementById("show-comment-form");
    const formContainer = document.getElementById("comment-form-container");
    const cancelBtn = document.getElementById("cancel-comment");

    // Проверка существования всех элементов на странице
    if (showBtn && formContainer && cancelBtn) {

        // Показ формы добавления комментария
        showBtn.addEventListener("click", () => {
            formContainer.style.display = "block";
            showBtn.disabled = true;
        });

        // Скрытие формы комментария при нажатии "Отмена"
        cancelBtn.addEventListener("click", () => {
          formContainer.style.display = "none";
          showBtn.disabled = false;
        });
    }

    // Обработка кнопок "Ответить" у комментариев

    const replyButtons = document.querySelectorAll(".reply-btn");
    const cancelReplyButtons = document.querySelectorAll(".cancel-reply-btn");

    // Показ формы ответа на конкретный комментарий и блокировка кнопки "Ответить"
    replyButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const commentId = btn.getAttribute("data-comment-id");
            const form = document.getElementById(`reply-form-${commentId}`);
            form.style.display = "block";
            btn.disabled = true;
        });
    });

     // Скрытие формы ответа и разблокировка кнопки "Ответить"
    cancelReplyButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const commentId = btn.getAttribute("data-comment-id");
            const form = document.getElementById(`reply-form-${commentId}`);
            form.style.display = "none";
            const replyBtn = document.querySelector(`.reply-btn[data-comment-id="${commentId}"]`);
            replyBtn.disabled = false;
        });
    });
});
