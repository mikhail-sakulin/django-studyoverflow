/*
    JS-скрипт для:
    - управления выбором тегов,
    - подсветки выбранных тегов,
    - фильтрации тегов по поиску,
    - добавления/удаления тегов через клик и ввод,
    - раскрытия/скрытия блока готовых тегов
*/


// Полная загрузка DOM
document.addEventListener('DOMContentLoaded', () => {

    const input = document.getElementById('id_tags');
    const search = document.getElementById('tag-search');
    const tags = document.querySelectorAll('#tags-container .tag-item');
    const toggleTagsBtn = document.getElementById('toggle-tags');
    const tagsWrapper = document.getElementById('tags-wrapper');

    // --- Функция нормализации тегов (аналог Python normalize_tag_name) ---
    function normalizeTagName(tagName) {
        if (!tagName) return '';
        tagName = tagName.trim().toLowerCase();
        tagName = tagName.replace(/\s+/g, "_");
        tagName = tagName.replace(/_+/g, "_");
        return tagName;
    }

    // --- Обновление подсветки выбранных тегов ---
    function updateSelectedTags() {
        let current = input.value.trim();
        let parts = current ? current.split(',').map(t => normalizeTagName(t)).filter(Boolean) : [];

        tags.forEach(tag => {
            const tagName = normalizeTagName(tag.getAttribute('data-tag'));
            tag.classList.toggle('selected', parts.includes(tagName));
        });
    }

    // --- Добавление/удаление тегов по клику ---
    tags.forEach(tag => {
        tag.addEventListener('click', () => {
            const tagName = normalizeTagName(tag.getAttribute('data-tag'));
            let current = input.value.trim();
            let parts = current ? current.split(',').map(t => normalizeTagName(t)).filter(Boolean) : [];

            if (!parts.includes(tagName)) {
                parts.push(tagName);
            } else {
                parts = parts.filter(t => t !== tagName);
            }

            input.value = parts.join(', ');
            updateSelectedTags();
        });
    });

    // --- Фильтрация тегов по поиску ---
    search.addEventListener('input', () => {
        const filter = normalizeTagName(search.value);
        tags.forEach(tag => {
            const tagName = normalizeTagName(tag.getAttribute('data-tag'));
            tag.style.display = tagName.includes(filter) ? 'block' : 'none';
        });
        updateSelectedTags();
    });

    // --- Обновление подсветки при ручном вводе ---
    input.addEventListener('input', updateSelectedTags);

    // --- Подсветка уже введённых тегов при загрузке страницы ---
    updateSelectedTags();

    // --- Раскрытие/скрытие блока готовых тегов ---
    toggleTagsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isHidden = tagsWrapper.style.display === 'none' || tagsWrapper.style.display === '';
        if (isHidden) {
            tagsWrapper.style.display = 'block';
            toggleTagsBtn.textContent = 'Скрыть готовые теги ▲';
            toggleTagsBtn.setAttribute('aria-expanded', 'true');
        } else {
            tagsWrapper.style.display = 'none';
            toggleTagsBtn.textContent = 'Выбрать готовые теги ▼';
            toggleTagsBtn.setAttribute('aria-expanded', 'false');
        }
    });

    // --- Блок тегов изначально скрыт через CSS, JS-скрипт ничего не меняет ---
});
