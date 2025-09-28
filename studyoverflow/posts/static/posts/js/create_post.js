/*
    JS-скрипт для:
    - управления окном предпросмотра,
    - рендера Markdown,
    - запуска подсветки синтаксиса кода
*/


// Полная загрузка DOM, чтобы код выполнился после построения структуры страницы
document.addEventListener("DOMContentLoaded", function() {

    // Получение ссылок на элементы страницы
    const textarea = document.getElementById("id_content");
    const preview = document.getElementById("content-preview");
    const wrapper = document.getElementById("preview-wrapper");
    const toggleBtn = document.getElementById("toggle-preview");
    const md = window.markdownit({ html: false, linkify: true, typographer: true });

    // Установка высоты блока предпросмотра равной высоте поля ввода содержимого поста
    preview.style.height = textarea.offsetHeight + "px";

    // Функция обновления содержимого предпросмотра
    function updatePreview() {
        // Преобразование текста из Markdown в HTML
        const html = md.render(textarea.value || "");

        // Вставка сгенерированного HTML в блок предпросмотра
        preview.innerHTML = html;

        // Подсветка синтаксиса в блоках кода (если предпросмотр виден)
        if (wrapper.style.display !== "none") {
            hljs.highlightAll();
        }
    }

    // Кнопка: показать/скрыть предпросмотр
    toggleBtn.addEventListener("click", (e) => {
        // Отмена действия отправки формы
        e.preventDefault();

        // Если предпросмотр скрыть - показать
        const isHidden = wrapper.style.display === "none" || wrapper.style.display === "";
        if (isHidden) {
            wrapper.style.display = "block";
            toggleBtn.textContent = "Скрыть предпросмотр форматирования ▲";
            toggleBtn.setAttribute("aria-expanded", "true");
            updatePreview();

        // Если предпросмотр показан - скрыть
        } else {
            wrapper.style.display = "none";
            toggleBtn.textContent = "Показать предпросмотр форматирования ▼";
            toggleBtn.setAttribute("aria-expanded", "false");
        }
    });

    // Обновление предпросмотра в реальном времени
    textarea.addEventListener("input", updatePreview);

    // Подготовка предпросмотра при загрузке страницы
    updatePreview();
});