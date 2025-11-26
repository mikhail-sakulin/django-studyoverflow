// Функция открытия окна
function openModal() {
    const modal = document.getElementById('global-image-modal');

    modal.classList.add('active');
}

// Функция закрытия окна
function closeModal() {
    const modal = document.getElementById('global-image-modal');
    modal.classList.remove('active');

    setTimeout(() => {
        document.getElementById('modal-image-container').innerHTML = '';
    }, 300);
}

// Закрытие по ESC
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeModal();
  }
});
