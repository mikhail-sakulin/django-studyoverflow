/*
    JS-скрипт для:
    - управления окном предпросмотра,
    - рендера Markdown,
    - запуска подсветки синтаксиса кода,
    - рендеринга математических формул (KaTeX).
*/


// Полная загрузка DOM, чтобы код выполнился после построения структуры страницы
document.addEventListener("DOMContentLoaded", function() {

    // Функция рендеринга формул в указанном контейнере
    function renderMath(container) {
        // Проверка, что KaTeX загружен и контейнер существует
        if (typeof katex === "undefined" || !container) return;

        // --- Блочные формулы (<div class="math">) ---
        container.querySelectorAll("div.math").forEach((el) => {
            // извлечение LaTeX-код
            const formula = el.textContent.trim();
            katex.render(formula, el, {
                // блочный режим (центрирование, крупный шрифт)
                displayMode: true,
                // не прерывать выполнение при ошибке
                throwOnError: false,
            });
        });

        // --- Инлайн-формулы (<span class="math-inline">) ---
        container.querySelectorAll(".math-inline").forEach((el) => {
            const formula = el.textContent.trim();
            katex.render(formula, el, {
                // внутри текста
                displayMode: false,
                throwOnError: false,
            });
        });
    }

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
            hljs.highlightAll();

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

    // --- Блок правил Markdown ---
    const rulesToggleBtn = document.getElementById("toggle-markdown-rules");
    const rulesWrapper = document.getElementById("markdown-rules-wrapper");
    let rulesRendered = false;

    if (rulesToggleBtn && rulesWrapper) {
        rulesToggleBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const isHidden = rulesWrapper.style.display === "none" || rulesWrapper.style.display === "";
            if (isHidden) {
                rulesWrapper.style.display = "block";
                rulesToggleBtn.textContent = "Скрыть наши правила синтаксиса Markdown и LaTeX ▲";
                rulesToggleBtn.setAttribute("aria-expanded", "true");
                // Рендер формул и подсветка синтаксиса в блоке правил
                if (!rulesRendered && typeof renderMath === "function") {
                    hljs.highlightAll();
                    renderMath(rulesWrapper);
                    rulesRendered = true;
                }
            } else {
                rulesWrapper.style.display = "none";
                rulesToggleBtn.textContent = "Показать наши правила синтаксиса Markdown и LaTeX ▼";
                rulesToggleBtn.setAttribute("aria-expanded", "false");
            }
        });
    }
});
