/*
    JS-скрипт для:
    - запуска подсветки синтаксиса кода Highlight.js после полной загрузки DOM
*/


// Выполнение после полной загрузки DOM
document.addEventListener("DOMContentLoaded", () => {

    // Объект hljs подключен из highlight.min.js

    // Запуск подсветки всех блоков <pre><code> на странице
    hljs.highlightAll();
});