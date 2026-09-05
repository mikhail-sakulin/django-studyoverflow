/*
    JS-скрипт для управления блоком правил синтаксиса Markdown и LaTeX:
    - показ/скрытие блока правил по кнопке;
    - рендер формул (KaTeX) и подсветка кода при первом открытии.
*/


document.addEventListener("DOMContentLoaded", function() {

    // Функция renderMath(container) подключена из katex_render.js
    // Объект hljs подключен из highlight.min.js

    const rulesToggleBtn = document.getElementById("toggle-markdown-rules");
    const rulesWrapper = document.getElementById("markdown-rules-wrapper");

    if (rulesToggleBtn && rulesWrapper) {
        rulesToggleBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const isHidden = rulesWrapper.style.display === "none" || rulesWrapper.style.display === "";
            if (isHidden) {
                rulesWrapper.style.display = "block";
                rulesToggleBtn.textContent = "Скрыть наши правила синтаксиса Markdown и LaTeX ▲";
                rulesToggleBtn.setAttribute("aria-expanded", "true");
                // Рендер формул и подсветка синтаксиса только внутри блока правил
                if (typeof hljs !== "undefined") {
                    rulesWrapper.querySelectorAll("pre code:not([data-highlighted])").forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }
                if (typeof renderMath === "function") renderMath(rulesWrapper);
            } else {
                rulesWrapper.style.display = "none";
                rulesToggleBtn.textContent = "Показать наши правила синтаксиса Markdown и LaTeX ▼";
                rulesToggleBtn.setAttribute("aria-expanded", "false");
            }
        });
    }
});
