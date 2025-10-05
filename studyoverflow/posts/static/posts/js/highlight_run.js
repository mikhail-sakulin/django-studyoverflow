/*
    JS-скрипт для:
    - инициализации подсветки синтаксиса кода
    - запуска Highlight.js после полной загрузки DOM
*/


// Выполнение после полной загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    // Запуск подсветки всех блоков <pre><code> на странице
    hljs.highlightAll();
});