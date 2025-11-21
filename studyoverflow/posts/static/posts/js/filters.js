/*
    JS-скрипт для управления фильтрами и сортировкой постов:
    - Показ/скрытие формы фильтров
    - Выбор фильтров по комментариям
    - Выбор режима совпадения тегов
    - Автоматический выбор "Один тег" при заполнении тегов вручную
    - Сортировка постов
    - Направление сортировки (стрелки)
    - Управление кнопкой выбора готовых тегов
    - Очистка пустых GET-полей перед отправкой формы
*/

document.addEventListener("DOMContentLoaded", () => {

    /* ===== Показ/скрытие формы фильтров ===== */
    const toggle = document.getElementById("filters-toggle");
    const form = document.getElementById("filters-form");
    const text = document.getElementById("filters-toggle-text");
    const icon = document.getElementById("filters-toggle-icon");

    if (toggle && form && text && icon) {
        toggle.addEventListener("click", () => {
            const isHidden = form.classList.contains("filters-hidden");

            if (isHidden) {
                // Показ формы
                form.classList.remove("filters-hidden");
                form.classList.add("filters-visible");

                text.textContent = "Скрыть фильтрацию и сортировку";
                icon.textContent = "⮝";
            } else {
                // Скрытие формы
                form.classList.remove("filters-visible");
                form.classList.add("filters-hidden");

                text.textContent = "Выбрать фильтрацию и сортировку";
                icon.textContent = "⮟";
            }
        });
    }

    /* ===== Фильтры по комментариям ===== */
    document.querySelectorAll(".comment-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = document.getElementById("has_comments_input");

            if (btn.classList.contains("active")) {
                // Если кнопка уже активна — снимается активность и очищается input
                btn.classList.remove("active");
                if (input) input.value = '';
            } else {
                // Активация текущей кнопки, деактивация остальных
                document.querySelectorAll(".comment-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                if (input) input.value = btn.dataset.value;
            }
        });
    });

    /* ===== Выбор режима совпадения по тегам ===== */
    document.querySelectorAll(".tag-match-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = document.getElementById("tag_match_input");

            if (btn.classList.contains("active")) {
                // Снятие выделения (сброс)
                btn.classList.remove("active");
                if (input) input.value = '';
            } else {
                // Активация текущей кнопки, деактивация остальных
                document.querySelectorAll(".tag-match-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                if (input) input.value = btn.dataset.value;
            }
        });
    });

    /* ===== Автоматический выбор "any" если введены теги ===== */
    const tagsInput = document.getElementById("id_tags");
    const tagMatchInput = document.getElementById("tag_match_input");

    if (tagsInput && tagMatchInput) {
        const cleanTags = tagsInput.value.replace(/[, ]/g, '').trim();

        if (cleanTags !== "" && tagMatchInput.value === "") {
            // Автоматически выбирается режим "any"
            tagMatchInput.value = "any";

            document.querySelectorAll(".tag-match-btn").forEach(btn => {
                if (btn.dataset.value === "any") {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                }
            });
        }
    }

    /* ===== Сортировка постов ===== */
    document.querySelectorAll(".sort-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = document.getElementById("sort_input");

            if (btn.classList.contains("active")) {
                // Деактивация кнопки
                btn.classList.remove("active");
                if (input) input.value = '';
            } else {
                // Активация текущей кнопки, деактивация остальных
                document.querySelectorAll(".sort-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                if (input) input.value = btn.dataset.value;
            }
        });
    });

    /* ===== Стрелки направления сортировки ===== */
    document.querySelectorAll(".order-arrow-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = document.getElementById("order_input");

            if (btn.classList.contains("active")) {
                btn.classList.remove("active");
                if (input) input.value = '';
            } else {
                document.querySelectorAll(".order-arrow-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                if (input) input.value = btn.dataset.value;
            }
        });
    });

    /* ===== Кнопка выбора готовых тегов ===== */
    const toggleTagsBtn = document.getElementById('toggle-tags');

    if (toggleTagsBtn) {
        function updateToggleTagsText() {
            let text = toggleTagsBtn.textContent;
            text = text.replace('готовые ', '');
            toggleTagsBtn.textContent = text;
        }

        toggleTagsBtn.addEventListener('click', () => {
            updateToggleTagsText();
        });

        // Инициализация при загрузке
        updateToggleTagsText();
    }

    /* ===== Очистка пустых GET-полей перед отправкой формы ===== */
    if (form) {
        form.addEventListener("submit", () => {
            const elements = form.querySelectorAll("input, select, textarea");

            elements.forEach(el => {
                if (el.type !== "submit" && (!el.value || el.value.trim() === "")) {
                    // чтобы пустые поля не попадали в GET-запрос
                    el.disabled = true;
                }
            });
        });
    }

});
