/*
    JS-скрипт для:
    - отображения полноразмерных аватарок пользователей в модальном окне,
    - обработки индикатора загрузки изображения,
    - поддержки динамически подгружаемых через HTMX элементов,
    - управления закрытием модального окна.
*/


(function () {
    // Получение ссылок на элементы модального окна
    const modal = document.getElementById('global-image-modal');
    const modalImg = document.getElementById('modal-avatar-img');
    const loadingIndicator = document.getElementById('modal-loading-indicator');

    // Проверка наличия обязательных элементов на странице
    if (!modal || !modalImg) return;

    // Функция открытия модального окна
    function openModal() {
        modal.classList.add('active');
    }

    // Функция закрытия модального окна и очистки контейнера
    window.closeModal = function () {
        modal.classList.remove('active');

        setTimeout(() => {
            modalImg.src = '';
            modalImg.alt = '';
        }, 300);
    };

    // Показ индикатора загрузки изображения
    function showLoading() {
        if (loadingIndicator) loadingIndicator.classList.add('is-loading');
        modalImg.classList.add('is-loading');
    }

    // Скрытие индикатора загрузки изображения
    function hideLoading() {
        if (loadingIndicator) loadingIndicator.classList.remove('is-loading');
        modalImg.classList.remove('is-loading');
    }

    // Обработчики успешной загрузки и ошибки загрузки картинки
    modalImg.addEventListener('load', hideLoading);
    modalImg.addEventListener('error', hideLoading);

    // Закрытие модального окна по нажатию клавиши Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            window.closeModal();
        }
    });

    // Делегирование события клика по аватаркам (включая подгруженные через HTMX)
    document.addEventListener('click', function (e) {
        // Поиск кликнутого элемента с классом аватара
        const trigger = e.target.closest('.avatar-trigger');
        if (!trigger) return;

        // Получение ссылки на полноразмерное изображение из dataset
        const fullUrl = trigger.dataset.fullAvatar;
        if (!fullUrl) return;

        // Активация индикатора загрузки и установка атрибутов картинки
        showLoading();
        modalImg.alt = trigger.alt || '';
        modalImg.src = fullUrl;

        // Открытие модального окна
        openModal();

        // Проверка на случай, если изображение уже загружено из кэша браузера
        if (modalImg.complete) {
            hideLoading();
        }
    });
})();
