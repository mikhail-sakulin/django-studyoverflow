/*
    Скрипт для анимированной смены фраз некоторых it-профессий
    в блоке с id="changing-text"
*/


// Полная загрузка DOM, чтобы работать с элементами страницы
document.addEventListener('DOMContentLoaded', () => {

    // Набор it-профессий, поочередно показывающихся в динамическом блоке
    const phrases = [
      "web-разработчика",
      "разработчика игр",
      "системного администратора",
      "data scientist'а"
    ];

    // Контейнер c id="changing-text", куда вставляются фразы
    const container = document.getElementById('changing-text');

    // Время показа каждой фразы в мс
    const DURATION = 2500;

    // Длительность анимации (из CSS-переменной --anim-duration)
    const ANIM = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--anim-duration')) || 1000;

    // Функция создания <span> с фразой и классами для анимации
    function makeSpan(text, extraClass='') {
      const s = document.createElement('span');
      s.className = 'phrase ' + extraClass;
      s.textContent = text;
      return s;
    }

    let idx = 0;

    // Создание <span> и добавление его в контейнер с классом "in" - появление
    let currentSpan = makeSpan(phrases[idx], 'in');
    container.appendChild(currentSpan);

    // Устанавливается размер контейнера, равный размеру текущего <span> (фразы)
    requestAnimationFrame(() => {
      const r = currentSpan.getBoundingClientRect();
      container.style.width = Math.ceil(r.width) + 'px';
      container.style.height = Math.ceil(r.height) + 'px';
    });

    // Функция показа следующей фразы
    function showNext() {
      const nextIdx = (idx + 1) % phrases.length;
      const nextSpan = makeSpan(phrases[nextIdx], 'from-top');
      container.appendChild(nextSpan);

      // Устанавливается размер контейнера под новый <span>
      requestAnimationFrame(() => {
        const r = nextSpan.getBoundingClientRect();
        container.style.width = Math.ceil(r.width) + 'px';
        container.style.height = Math.ceil(r.height) + 'px';

        // Ожидание применения стартовых стилей,
        // затем смена класса для запуска анимации появления
        setTimeout(() => {
          nextSpan.classList.remove('from-top');
          nextSpan.classList.add('in');

          // Удаление предыдущего <span> из DOM
          if (currentSpan && currentSpan.parentNode) {
            currentSpan.parentNode.removeChild(currentSpan);
          }

          // Обновление текущего <span> и idx
          currentSpan = nextSpan;
          idx = nextIdx;
        }, 70);
      });
    }

    // Запуск показа следующей фразы каждые DURATION мс
    setInterval(showNext, DURATION);
  });