class FlappyKiroApp {
    constructor() {
        this.currentScreen = 'menu';
        this.selectedDifficulty = 'medium';
        this.game = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.showScreen('menu');
        
        telemetry.info('App initialized');
    }

    initializeElements() {
        this.screens = {
            menu: document.getElementById('menu-screen'),
            game: document.getElementById('game-screen'),
            gameOver: document.getElementById('game-over-screen'),
            leaderboard: document.getElementById('leaderboard-screen')
        };
        
        this.canvas = document.getElementById('game-canvas');
        this.scoreDisplay = document.getElementById('score');
        this.difficultyDisplay = document.getElementById('difficulty-display');
    }

    setupEventListeners() {
        // Difficulty selection
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectDifficulty(e.target.dataset.difficulty);
            });
        });

        // Menu buttons
        document.getElementById('start-game').addEventListener('click', () => {
            this.startGame();
        });

        document.getElementById('show-leaderboard').addEventListener('click', () => {
            this.showLeaderboard();
        });

        // Game over buttons
        document.getElementById('submit-score').addEventListener('click', () => {
            this.submitScore();
        });

        document.getElementById('play-again').addEventListener('click', () => {
            this.startGame();
        });

        document.getElementById('back-to-menu').addEventListener('click', () => {
            this.showScreen('menu');
        });

        // Leaderboard button
        document.getElementById('back-from-leaderboard').addEventListener('click', () => {
            this.showScreen('menu');
        });

        // Game over event
        document.addEventListener('gameOver', (e) => {
            this.handleGameOver(e.detail);
        });

        // Username input validation
        document.getElementById('username').addEventListener('input', (e) => {
            this.validateUsername(e.target);
        });
    }

    selectDifficulty(difficulty) {
        this.selectedDifficulty = difficulty;
        
        // Update UI
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.classList.remove('selected');
        });
        document.querySelector(`[data-difficulty="${difficulty}"]`).classList.add('selected');
        
        telemetry.info('Difficulty selected', { difficulty });
    }

    showScreen(screenName) {
        // Hide all screens
        Object.values(this.screens).forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Show selected screen
        this.screens[screenName].classList.add('active');
        this.currentScreen = screenName;
        
        telemetry.debug('Screen changed', { screen: screenName });
    }

    startGame() {
        this.showScreen('game');
        
        // Initialize game
        this.game = new FlappyKiroGame(this.canvas);
        this.game.setDifficulty(this.selectedDifficulty);
        
        // Update UI
        this.difficultyDisplay.textContent = `Difficulty: ${this.selectedDifficulty.charAt(0).toUpperCase() + this.selectedDifficulty.slice(1)}`;
        this.updateScore(0);
        
        // Start game loop for UI updates
        this.startUIUpdates();
        
        // Start the game
        this.game.start();
    }

    startUIUpdates() {
        const updateUI = () => {
            if (this.game && this.game.gameRunning) {
                this.updateScore(this.game.getScore());
                requestAnimationFrame(updateUI);
            }
        };
        updateUI();
    }

    updateScore(score) {
        this.scoreDisplay.textContent = `Score: ${score}`;
    }

    handleGameOver(gameData) {
        document.getElementById('final-score').textContent = `Final Score: ${gameData.score}`;
        this.showScreen('gameOver');
    }

    validateUsername(input) {
        const username = input.value;
        const isValid = /^[a-zA-Z0-9_-]{1,20}$/.test(username) && 
                       !this.containsInappropriateContent(username);
        
        input.style.borderColor = isValid ? '#4CAF50' : '#f44336';
        document.getElementById('submit-score').disabled = !isValid;
        
        return isValid;
    }

    containsInappropriateContent(username) {
        const inappropriateWords = ['admin', 'root', 'test', 'null', 'undefined'];
        return inappropriateWords.some(word => 
            username.toLowerCase().includes(word.toLowerCase())
        );
    }

    async submitScore() {
        const username = document.getElementById('username').value;
        
        if (!this.validateUsername(document.getElementById('username'))) {
            alert('Please enter a valid username (alphanumeric, underscore, hyphen only, 1-20 characters)');
            return;
        }

        const scoreData = {
            username: username,
            score: this.game.getScore(),
            difficulty: this.game.getDifficulty(),
            timestamp: new Date().toISOString()
        };

        try {
            const response = await fetch('/api/scores', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(scoreData)
            });

            if (response.ok) {
                telemetry.scoreSubmitted(username, scoreData.score, scoreData.difficulty);
                alert('Score submitted successfully!');
                document.getElementById('username').value = '';
            } else {
                const error = await response.json();
                alert(`Failed to submit score: ${error.message}`);
                telemetry.error('Score submission failed', { error: error.message });
            }
        } catch (error) {
            alert('Failed to submit score. Please try again.');
            telemetry.error('Score submission error', { error: error.message });
        }
    }

    async showLeaderboard() {
        this.showScreen('leaderboard');
        
        try {
            const response = await fetch('/api/leaderboard');
            const leaderboard = await response.json();
            
            this.renderLeaderboard(leaderboard);
            telemetry.info('Leaderboard loaded', { entries: leaderboard.length });
        } catch (error) {
            document.getElementById('leaderboard-content').innerHTML = 
                '<p>Failed to load leaderboard. Please try again.</p>';
            telemetry.error('Leaderboard load failed', { error: error.message });
        }
    }

    renderLeaderboard(leaderboard) {
        const content = document.getElementById('leaderboard-content');
        
        if (leaderboard.length === 0) {
            content.innerHTML = '<p>No scores yet. Be the first to play!</p>';
            return;
        }

        const html = leaderboard.map((entry, index) => `
            <div class="leaderboard-entry">
                <span class="leaderboard-rank">#${index + 1}</span>
                <span>${entry.username}</span>
                <span>${entry.score} (${entry.difficulty})</span>
            </div>
        `).join('');
        
        content.innerHTML = html;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FlappyKiroApp();
});