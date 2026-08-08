/*
    JS-скрипт для кнопки "..." в пагинации:
    - по клику превращает её в поле ввода номера страницы,
    - по Enter переходит на введённую страницу с сохранением всех GET-параметров,
    - по Escape - возвращает обратно кнопку "...".
*/


document.addEventListener("DOMContentLoaded", function () {

    const jumpItems = document.querySelectorAll(".page-jump");
    let blurCloseTimer = null;

    /* Закрытие формы ввода страницы и сброс таймера */
    function closeJump(item) {
        clearTimeout(blurCloseTimer);
        item.classList.remove("page-jump-open");
    }

    /* Открытие формы ввода, закрытие остальных элементов и фокус на инпуте */
    function openJump(item) {
        jumpItems.forEach(function (other) {
            if (other !== item) {
                closeJump(other);
            }
        });

        const input = item.querySelector(".page-jump-input");
        input.value = "";
        input.size = 2;

        item.classList.add("page-jump-open");

        requestAnimationFrame(function () {
            input.focus();
        });
    }

    /* Проверка введенного номера страницы (от 1 до maxPage) и редирект на нужный URL */
    function goToPage(item) {
        const input = item.querySelector(".page-jump-input");
        const maxPage = parseInt(input.dataset.maxPage, 10);
        let page = parseInt(input.value, 10);

        if (!page || page < 1) {
            page = 1;
        } else if (page > maxPage) {
            page = maxPage;
        }

        window.location.href = input.dataset.baseUrl + page;
    }

    jumpItems.forEach(function (item) {
        const toggleBtn = item.querySelector(".page-jump-toggle");
        const input = item.querySelector(".page-jump-input");

        /* Открытие формы по клику на кнопку троеточия */
        toggleBtn.addEventListener("click", function () {
            openJump(item);
        });

        /* Ограничение ввода только цифрами и динамическое изменение ширины поля */
        input.addEventListener("input", function () {
            input.value = input.value.replace(/\D/g, "");
            input.size = Math.max(2, input.value.length);
        });

        /* Обработка нажатий клавиш: Enter — переход, Escape — закрытие */
        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                goToPage(item);
            } else if (event.key === "Escape") {
                closeJump(item);
            }
        });

        /* Отложенное закрытие для корректной работы кликов */
        input.addEventListener("blur", function () {
            blurCloseTimer = setTimeout(function () {
                closeJump(item);
            }, 500);
        });
    });

    /* Закрывает форму, если кликнули вне неё */
    document.addEventListener("mouseup", function (event) {
        const openItem = document.querySelector(".page-jump-open");
        if (openItem && !openItem.contains(event.target)) {
            closeJump(openItem);
        }
    });

});
