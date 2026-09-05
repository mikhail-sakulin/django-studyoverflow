/*
    JS-скрипт для рендеринга математических формул через KaTeX:
    - Инлайн-формулы: <span class="math-inline">LaTeX-код</span>;
    - Блочные формулы: <div class="math">LaTeX-код</div>;
    - Автоматический рендеринг при загрузке страницы и после HTMX-обновлений.
*/


// Функция рендеринга формул в указанном контейнере
function renderMath(container) {
    // Проверка, что KaTeX загружен и контейнер существует
    if (typeof katex === "undefined" || !container) return;

    // --- Блочные формулы (<div class="math">) ---
    container.querySelectorAll("div.math:not([data-katex-rendered])").forEach((el) => {
        // извлечение LaTeX-код
        const formula = el.textContent.trim();
        katex.render(formula, el, {
            // блочный режим (центрирование, крупный шрифт)
            displayMode: true,
            // не прерывать выполнение при ошибке
            throwOnError: false,
        });
        // Добавление защитного атрибута к элементу, чтобы не было повторного рендера KaTeX
        el.setAttribute("data-katex-rendered", "true");
    });

    // --- Инлайн-формулы (<span class="math-inline">) ---
    container.querySelectorAll(".math-inline:not([data-katex-rendered])").forEach((el) => {
        const formula = el.textContent.trim();
        katex.render(formula, el, {
            // внутри текста
            displayMode: false,
            throwOnError: false,
        });
        // Добавление защитного атрибута к элементу, чтобы не было повторного рендера KaTeX
        el.setAttribute("data-katex-rendered", "true");
    });
}

// Первоначальный рендер при загрузке страницы
document.addEventListener("DOMContentLoaded", () => {
    renderMath(document.body);
});

// Рендер после каждого HTMX-обновления
document.body.addEventListener("htmx:afterSwap", (event) => {
    // рендер только в обновлённой части
    renderMath(event.target);
});
