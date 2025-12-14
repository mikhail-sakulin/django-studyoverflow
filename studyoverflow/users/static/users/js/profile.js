/*
    JS-скрипт для:
    - управления формой редактирования профиля,
    - подтверждения удаления аккаунта
*/


document.addEventListener('DOMContentLoaded', function() {

    // Получение ссылок на элементы интерфейса
    const editFormContainer = document.getElementById('edit-form-container');
    const toggleEditBtn = document.getElementById('toggle-edit-btn');

    // Скрытие формы редактирования при загрузке страницы
    if (editFormContainer) {
        editFormContainer.style.display = 'none';
    }

    // Обработка нажатия кнопки "Редактировать профиль"
    if (toggleEditBtn) {
        toggleEditBtn.addEventListener('click', function(event) {
            // Отмена стандартного поведения ссылки
            event.preventDefault();

            // Переключение состояния отображения формы
            if (editFormContainer.style.display === 'none') {
                editFormContainer.style.display = 'block';
                toggleEditBtn.textContent = 'Скрыть форму';

                // Плавная прокрутка к форме
                editFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                editFormContainer.style.display = 'none';
                toggleEditBtn.textContent = 'Редактировать профиль';
            }
        });
    }

    // Функция подтверждения удаления аккаунта
    window.confirmDelete = function() {
        return confirm("Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо!");
    };

    // Проверка наличия ошибок в форме
    const hasErrors =
        editFormContainer.querySelector('.alert-danger') !== null ||
        editFormContainer.querySelector('.text-danger div') !== null;

    // Если в форме есть ошибки — показать форму и прокрутить к ней
    if (hasErrors) {
        editFormContainer.style.display = 'block';
        if (toggleEditBtn) toggleEditBtn.textContent = 'Скрыть форму';
        editFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
