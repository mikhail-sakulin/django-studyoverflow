/*
    JS-скрипт для:
    - добавления градиента/эффекта обрезки к content,
      если его содержимое превышает разрешенную высоту
*/


// Выполнение после полной загрузки DOM
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.content').forEach(content => {
        if (content.scrollHeight > content.clientHeight) {
            // Добавляется класс overflow для применения эффекта
            content.classList.add('overflow');
        }
    });
});