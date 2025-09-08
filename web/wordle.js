document.addEventListener('DOMContentLoaded', () => {
    const gameBoard = document.getElementById('game-board');
    const inputs = [];
    const metaEl = document.getElementById('meta');
    let tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
    if (tg && tg.initDataUnsafe) {
        tg.expand && tg.expand();
    }

    // Данные Telegram WebApp
    let userId = 0;
    let username = '';
    let chatId = 0; // ожидаем, что миниапп открыт из канала/чата

    if (tg && tg.initDataUnsafe) {
        const user = tg.initDataUnsafe.user || {};
        userId = user.id || 0;
        username = user.username || (user.first_name || '') + (user.last_name ? ('_' + user.last_name) : '');
        // chatId можно передать через start_param или через tg.initDataUnsafe.start_param
        // Для простоты попробуем прочитать через query string
    }

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('chat_id')) {
        chatId = parseInt(urlParams.get('chat_id')) || 0;
    }

    async function apiToday() {
        const qs = new URLSearchParams({ chat_id: String(chatId || 0), user_id: String(userId || 0) });
        const res = await fetch(`/api/wordle/today?${qs.toString()}`);
        if (!res.ok) throw new Error('API error');
        return res.json();
    }

    async function apiGuess(guess) {
        const res = await fetch('/api/wordle/guess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ guess, chat_id: chatId, user_id: userId, username })
        });
        if (!res.ok) throw new Error('API error');
        return res.json();
    }

    function createBoard() {
        for (let i = 0; i < 30; i++) {
            const input = document.createElement('input');
            input.type = 'text';
            input.maxLength = 1;
            input.classList.add('tile-input');
            input.id = `input-${Math.floor(i / 5)}-${i % 5}`;
            input.setAttribute('data-row', Math.floor(i / 5));
            input.setAttribute('data-col', i % 5);

            // Disable all but the first row initially
            if (Math.floor(i / 5) !== 0) {
                input.disabled = true;
            }

            gameBoard.appendChild(input);
            inputs.push(input);
        }
    }

    function attachEventListeners() {
        inputs.forEach((input, index) => {
            input.addEventListener('input', (e) => {
                // Automatically move to the next input
                const col = parseInt(e.target.getAttribute('data-col'));
                if (e.target.value && col < 4) {
                    const nextInput = document.getElementById(`input-${e.target.getAttribute('data-row')}-${col + 1}`);
                    nextInput.focus();
                }
            });

            input.addEventListener('keydown', (e) => {
                const row = parseInt(e.target.getAttribute('data-row'));
                const col = parseInt(e.target.getAttribute('data-col'));

                if (e.key === 'Backspace' && !e.target.value && col > 0) {
                    const prevInput = document.getElementById(`input-${row}-${col - 1}`);
                    prevInput.focus();
                } else if (e.key === 'Enter' && col === 4) {
                    checkWord(row);
                }
            });

            input.addEventListener('focus', (e) => {
                e.target.select();
            });
        });
    }

    async function checkWord(row) {
        let guess = '';
        for (let i = 0; i < 5; i++) {
            const input = document.getElementById(`input-${row}-${i}`);
            guess += input.value;
            input.disabled = true; // Disable current row
        }

        guess = guess.toLowerCase();

        if (guess.length !== 5) return;

        try {
            const resp = await apiGuess(guess);
            if (resp.error) {
                alert(resp.error);
                return;
            }

            const tiles = resp.tiles || [];
            for (let i = 0; i < 5; i++) {
                const input = document.getElementById(`input-${row}-${i}`);
                input.classList.add(tiles[i] || 'absent');
            }

            if (metaEl) {
                // обновим счетчик попыток
                metaEl.textContent = `Попыток сегодня: ${resp.attempts_made || 0} / 6`;
            }

            if (resp.has_win) {
                setTimeout(() => alert('Вы победили!'), 100);
            } else if (!resp.is_finished && row < 5) {
                for (let i = 0; i < 5; i++) {
                    const nextInput = document.getElementById(`input-${row + 1}-${i}`);
                    nextInput.disabled = false;
                }
                document.getElementById(`input-${row + 1}-0`).focus();
            } else if (resp.is_finished) {
                setTimeout(() => alert('Вы проиграли!'), 100);
            }
        } catch (e) {
            alert('Ошибка соединения с сервером');
        }
    }

    // Setup
    createBoard();
    attachEventListeners();
    // Инициализируем состояние дня и попыток
    apiToday().then((state) => {
        if (metaEl) {
            metaEl.textContent = `Попыток сегодня: ${state.attempts_made || 0} / ${state.max_attempts || 6}`;
        }
        // если уже есть попытки, разблокируем следующую строку
        const attempts = state.attempts_made || 0;
        const finished = state.is_finished;
        if (finished) return; // все заблокировано
        const nextRow = attempts;
        for (let i = 0; i < 5; i++) {
            const input = document.getElementById(`input-${nextRow}-${i}`);
            input.disabled = false;
        }
        document.getElementById(`input-${nextRow}-0`).focus();
    }).catch(() => {
        // при ошибке оставим дефолтное состояние (только первая строка активна)
    });
    // Let the user tap the first input to start
});