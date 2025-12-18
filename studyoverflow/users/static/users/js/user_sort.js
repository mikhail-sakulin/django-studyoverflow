/*
    JS-скрипт для:
    - управления фильтром пользователей по онлайн-статусу,
    - управления сортировкой списка пользователей,
    - переключения порядка сортировки (по возрастанию / убыванию),
    - синхронизации активных кнопок с hidden-input полями формы
*/


document.body.addEventListener('click', (event) => {

    // ===== ФИЛЬТР ОНЛАЙН =====
    const onlineBtn = event.target.closest('.user-online-btn');
    if (onlineBtn) {
        const input = document.getElementById('online_input');
        onlineBtn.closest('.btn-group')
            .querySelectorAll('.user-online-btn')
            .forEach(b => b.classList.remove('active'));

        onlineBtn.classList.add('active');
        input.value = onlineBtn.dataset.value;
        return;
    }

    // ===== СОРТИРОВКА =====
    const sortBtn = event.target.closest('.user-sort-btn');
    if (sortBtn) {
        const input = document.getElementById('user_sort_input');
        sortBtn.closest('.btn-group')
            .querySelectorAll('.user-sort-btn')
            .forEach(b => b.classList.remove('active'));

        sortBtn.classList.add('active');
        input.value = sortBtn.dataset.value;
        return;
    }

    // ===== ПОРЯДОК =====
    const orderBtn = event.target.closest('.user-order-btn');
    if (orderBtn) {
        const input = document.getElementById('user_order_input');
        orderBtn.parentElement
            .querySelectorAll('.user-order-btn')
            .forEach(b => b.classList.remove('active'));

        orderBtn.classList.add('active');
        input.value = orderBtn.dataset.value;
    }

});
