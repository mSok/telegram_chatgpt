document.addEventListener('DOMContentLoaded', () => {
    const gameBoard = document.getElementById('game-board');
    const words = ["пицца", "школа", "кошка", "собор", "книга"];
    let secretWord = words[Math.floor(Math.random() * words.length)];

    const inputs = [];

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

    function checkWord(row) {
        let guess = '';
        for (let i = 0; i < 5; i++) {
            const input = document.getElementById(`input-${row}-${i}`);
            guess += input.value;
            input.disabled = true; // Disable current row
        }

        guess = guess.toLowerCase();

        if (guess.length !== 5) return;

        for (let i = 0; i < 5; i++) {
            const input = document.getElementById(`input-${row}-${i}`);
            const letter = guess[i];

            if (letter === secretWord[i]) {
                input.classList.add('correct');
            } else if (secretWord.includes(letter)) {
                input.classList.add('present');
            } else {
                input.classList.add('absent');
            }
        }

        if (guess === secretWord) {
            setTimeout(() => alert('Вы победили!'), 100);
            // Game over, do nothing more
        } else if (row < 5) {
            // Enable next row
            for (let i = 0; i < 5; i++) {
                const nextInput = document.getElementById(`input-${row + 1}-${i}`);
                nextInput.disabled = false;
            }
            // Focus the first input of the next row
            document.getElementById(`input-${row + 1}-0`).focus();
        } else {
            setTimeout(() => alert(`Вы проиграли! Загаданное слово: ${secretWord}`), 100);
        }
    }

    // Setup
    createBoard();
    attachEventListeners();
    // Let the user tap the first input to start
});