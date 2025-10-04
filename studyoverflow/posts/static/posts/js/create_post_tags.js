/*
    JS-скрипт для:
    - управления выбором тегов,
    - подсветки выбранных тегов,
    - фильтрации тегов по поиску,
    - добавления/удаления тегов через клик и ввод,
    - раскрытия/скрытия блока готовых тегов
*/


// Полная загрузка DOM, чтобы код выполнялся после построения структуры страницы
document.addEventListener('DOMContentLoaded', () => {

    // Получение ссылок на элементы страницы
    const input = document.getElementById('id_tags');
    const search = document.getElementById('tag-search');
    const tags = document.querySelectorAll('#tags-container .tag-item');
    const toggleTagsBtn = document.getElementById('toggle-tags');
    const tagsWrapper = document.getElementById('tags-wrapper');

    // Обновление подсветки выбранных тегов
    function updateSelectedTags() {
        let current = input.value.trim();
        let parts = current ? current.split(',').map(t => t.trim().toLowerCase()).filter(Boolean) : [];

        tags.forEach(tag => {
            const tagName = tag.getAttribute('data-tag').toLowerCase();
            tag.classList.toggle('selected', parts.includes(tagName));
        });
    }

    // Добавление/удаление тегов по клику
    tags.forEach(tag => {
        tag.addEventListener('click', () => {
            const tagName = tag.getAttribute('data-tag');
            let current = input.value.trim();
            let parts = current ? current.split(',').map(t => t.trim()).filter(Boolean) : [];

            if (!parts.includes(tagName)) {
                parts.push(tagName);
            } else {
                parts = parts.filter(t => t.toLowerCase() !== tagName.toLowerCase());
            }

            // Обновление поля ввода и подсветки
            input.value = parts.join(', ');
            updateSelectedTags();
        });
    });

    // Фильтрация тегов по поиску
    search.addEventListener('input', () => {
        const filter = search.value.toLowerCase();
        tags.forEach(tag => {
            const tagName = tag.getAttribute('data-tag').toLowerCase();
            tag.style.display = tagName.includes(filter) ? 'block' : 'none';
        });
        updateSelectedTags();
    });

    // Обновление подсветки при ручном вводе
    input.addEventListener('input', updateSelectedTags);

    // Подсветка уже введённых тегов при загрузке страницы
    updateSelectedTags();

    // Раскрытие/скрытие блока готовых тегов
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

    // Блок тегов изначально скрыт через CSS, JS-скрипт ничего не меняет
});
