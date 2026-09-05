/*
    JS-скрипт для:
    - управления окном предпросмотра,
    - рендера Markdown,
    - запуска подсветки синтаксиса кода,
    - рендеринга математических формул (KaTeX).
*/


// Полная загрузка DOM, чтобы код выполнился после построения структуры страницы
document.addEventListener("DOMContentLoaded", function() {

    // Функция renderMath подключена из katex_render.js
    // Объект hljs подключен из highlight.min.js

    // Получение ссылок на элементы страницы
    const textarea = document.getElementById("id_content");
    const preview = document.getElementById("content-preview");
    const wrapper = document.getElementById("preview-wrapper");
    const toggleBtn = document.getElementById("toggle-preview");
    const md = window.markdownit({ html: true, linkify: true, typographer: true, breaks: true }).use(window.markdownitTaskLists, { enabled: true });

    // Установка высоты блока предпросмотра равной высоте поля ввода содержимого поста
    preview.style.height = textarea.offsetHeight + "px";

    // Заменяет инлайн-формулы <span class="math-inline"> на уникальные плейсхолдеры
    // для защиты синтаксиса LaTeX от искажения при рендере Markdown.
    function protectMathInline(content) {
        const mathExpressions = [];

        const protectedContent = content.replace(
            /<span class="math-inline">.*?<\/span>/gs,
            (match) => {
                const placeholder = `MATHINLINEBLOCK${crypto.randomUUID().replaceAll("-", "")}`;

                mathExpressions.push({
                    placeholder: placeholder,
                    original: match,
                });

                return placeholder;
            }
        );

        return {
            content: protectedContent,
            mathExpressions: mathExpressions,
        };
    }

    // Функция обновления содержимого предпросмотра
    function updatePreview() {
        const {
            content,
            mathExpressions,
        } = protectMathInline(textarea.value || "");

        // Markdown рендерится уже без math-inline блоков.
        let html = md.render(content);

        // Возвращается math-inline в исходном виде.
        mathExpressions.forEach(({ placeholder, original }) => {
            html = html.replace(placeholder, original);
        });

        preview.innerHTML = html;

        if (wrapper.style.display !== "none") {
            if (typeof hljs !== "undefined") {
                preview.querySelectorAll("pre code").forEach((block) => {
                    hljs.highlightElement(block);
                });
            }

            if (typeof renderMath === "function") {
                renderMath(preview);
            }
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
