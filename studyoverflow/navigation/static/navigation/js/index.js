/*
    Скрипт для анимированной смены фраз некоторых it-профессий в блоке с id="changing-text".
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

    // Задержка между началом пролистывания текущей фразы (ее смена) и
    // запуском анимации появления следующей фразы
    const OUT_DELAY = 150;

    // Функция создания <span> с фразой и классами для анимации
    function makeSpan(text, extraClass='') {
      const s = document.createElement('span');
      s.className = 'phrase ' + extraClass;
      s.textContent = text;
      return s;
    }

    let idx = 0;

    // Создание начального <span> со стартовыми классами для анимации появления сверху
    let currentSpan = makeSpan(phrases[idx], 'from-top');
    container.appendChild(currentSpan);

    // Устанавливается размер контейнера, равный размеру текущего <span> (фразы)
    requestAnimationFrame(() => {
        const r = currentSpan.getBoundingClientRect();
        container.style.width = Math.ceil(r.width) + 'px';
        container.style.height = Math.ceil(r.height) + 'px';

        // Ожидание применения стартовых стилей браузером,
        // затем смена класса для запуска первой анимации появления текста
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                currentSpan.classList.remove('from-top');
                currentSpan.classList.add('in');
            });
        });
    });

    // Функция показа следующей фразы
    function showNext() {
        const nextIdx = (idx + 1) % phrases.length;
        const oldSpan = currentSpan;

        // Запуск анимации ухода текущего <span>
        if (oldSpan) {
            oldSpan.classList.remove('in');
            oldSpan.classList.add('out');
        }

        // Удаление предыдущего <span> из DOM после завершения анимации ухода
        setTimeout(() => {
            if (oldSpan && oldSpan.parentNode) {
                oldSpan.parentNode.removeChild(oldSpan);
            }
        }, ANIM + 140);

        // Ожидание задержки, затем создание и появление нового <span>
        setTimeout(() => {
            const nextSpan = makeSpan(phrases[nextIdx], 'from-top');
            container.appendChild(nextSpan);

            requestAnimationFrame(() => {
                const r = nextSpan.getBoundingClientRect();
                container.style.width = Math.ceil(r.width) + 'px';
                container.style.height = Math.ceil(r.height) + 'px';

                // Ожидание применения стартовых стилей,
                // затем смена класса для запуска анимации появления
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        nextSpan.classList.remove('from-top');
                        nextSpan.classList.add('in');
                    });
                });
            });

            // Обновление текущего <span> и idx
            currentSpan = nextSpan;
            idx = nextIdx;
        }, OUT_DELAY);
    }

    // Запуск показа следующей фразы каждые DURATION мс
    setInterval(showNext, DURATION);
});
