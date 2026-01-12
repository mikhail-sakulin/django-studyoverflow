/*
    JS-скрипт для управления показом полного текста комментария:
    - Раскрытие/сворачивание комментариев
    - Сохранение состояния комментариев (открыт/скрыт) по commentId
    - Затемнение текста для обрезанных комментариев
    - Скролл к комментарию
*/


(function () {

    const MAX_HEIGHT = 200;

    // commentId -> boolean (true = открыт)
    const commentState = new Map();

    // проверка, нужно ли ставить градиент
    function updateTruncation(content) {
        if (!content) return;
        const isTruncated = content.scrollHeight > MAX_HEIGHT + 5 && !content.classList.contains('is-expanded');
        content.classList.toggle('truncated', isTruncated);
    }

    // синхронизация состояния комментариев после HTMX swap
    function syncComments(root = document) {
        root.querySelectorAll('[data-comment-expand]').forEach(wrapper => {

            const commentId = wrapper.dataset.commentId;
            const content = document.getElementById(wrapper.dataset.target);
            if (!commentId || !content) return;

            const arrow = wrapper.querySelector('.comment-expand-arrow');
            const textNode = wrapper.querySelector('.comment-expand-btn');

            if (!commentState.has(commentId)) {
                commentState.set(commentId, false);
            }

            const expanded = commentState.get(commentId);

            content.style.transition = 'max-height 0.25s ease';

            if (expanded) {
                content.classList.add('is-expanded');
                content.style.maxHeight = content.scrollHeight + 'px';
                if (arrow) arrow.style.transform = 'rotate(180deg)';
                if (textNode) textNode.childNodes[0].textContent = 'Свернуть ';
            } else {
                content.classList.remove('is-expanded');
                content.style.maxHeight = MAX_HEIGHT + 'px';
                if (arrow) arrow.style.transform = 'rotate(0deg)';
                if (textNode) textNode.childNodes[0].textContent = 'Показать полностью ';
            }

            wrapper.style.display = content.scrollHeight > MAX_HEIGHT + 5 ? 'block' : 'none';

            updateTruncation(content);
        });
    }

    // проверка, видна ли верхняя граница элемента в viewport
    function isTopVisible(el) {
        const rect = el.getBoundingClientRect();
        return rect.top >= 0 && rect.top <= window.innerHeight;
    }

    // клик по кнопке раскрытия/сворачивания
    document.body.addEventListener('click', e => {
        const wrapper = e.target.closest('[data-comment-expand]');
        if (!wrapper) return;

        const commentId = wrapper.dataset.commentId;
        const content = document.getElementById(wrapper.dataset.target);
        if (!commentId || !content) return;

        const arrow = wrapper.querySelector('.comment-expand-arrow');
        const textNode = wrapper.querySelector('.comment-expand-btn');
        const anchorEl = document.getElementById(wrapper.dataset.scrollAnchor);

        const expanded = commentState.get(commentId);
        commentState.set(commentId, !expanded);

        if (expanded) {
            // Свернуть
            content.style.maxHeight = MAX_HEIGHT + 'px';
            content.classList.remove('is-expanded');
            if (arrow) arrow.style.transform = 'rotate(0deg)';
            if (textNode) textNode.childNodes[0].textContent = 'Показать полностью ';

            // Скролл, только если верх элемента вне viewport
            if (anchorEl && !isTopVisible(anchorEl)) {
                requestAnimationFrame(() => {
                    anchorEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
            }

        } else {
            // Открыть
            content.style.maxHeight = content.scrollHeight + 'px';
            content.classList.add('is-expanded');
            if (arrow) arrow.style.transform = 'rotate(180deg)';
            if (textNode) textNode.childNodes[0].textContent = 'Свернуть ';
        }

        updateTruncation(content);
    });

    document.body.addEventListener('htmx:afterSettle', e => {
        syncComments(e.target);
    });

})();
