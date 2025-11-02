class FlappyKiroGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.width = canvas.width;
        this.height = canvas.height;
        
        this.reset();
        this.setupDifficulties();
        
        // Bind event listeners
        this.handleKeyPress = this.handleKeyPress.bind(this);
    }

    setupDifficulties() {
        this.difficulties = {
            easy: {
                gravity: 0.3,
                jumpStrength: -6,
                wallSpeed: 2,
                gapSize: 200,
                wallSpacing: 300
            },
            medium: {
                gravity: 0.4,
                jumpStrength: -7,
                wallSpeed: 3,
                gapSize: 160,
                wallSpacing: 280
            },
            hard: {
                gravity: 0.5,
                jumpStrength: -8,
                wallSpeed: 4,
                gapSize: 120,
                wallSpacing: 250
            }
        };
    }

    reset() {
        this.ghosty = {
            x: 100,
            y: this.height / 2,
            width: 40,
            height: 40,
            velocity: 0
        };
        
        this.walls = [];
        this.score = 0;
        this.gameRunning = false;
        this.gameOver = false;
        this.lastWallX = this.width;
    }

    setDifficulty(difficulty) {
        this.difficulty = difficulty;
        this.config = this.difficulties[difficulty];
        telemetry.info('Difficulty set', { difficulty });
    }

    start() {
        this.reset();
        this.gameRunning = true;
        this.gameOver = false;
        
        // Add event listener for spacebar
        document.addEventListener('keydown', this.handleKeyPress);
        
        telemetry.gameStart(this.difficulty);
        this.gameLoop();
    }

    stop() {
        this.gameRunning = false;
        document.removeEventListener('keydown', this.handleKeyPress);
        telemetry.gameEnd(this.score, this.difficulty);
    }

    handleKeyPress(event) {
        if (event.code === 'Space' && this.gameRunning && !this.gameOver) {
            event.preventDefault();
            this.jump();
        }
    }

    jump() {
        this.ghosty.velocity = this.config.jumpStrength;
        telemetry.debug('Ghosty jumped', { velocity: this.ghosty.velocity });
    }

    update() {
        if (!this.gameRunning || this.gameOver) return;

        // Update Ghosty physics
        this.ghosty.velocity += this.config.gravity;
        this.ghosty.y += this.ghosty.velocity;

        // Generate walls
        if (this.walls.length === 0 || this.lastWallX - this.walls[this.walls.length - 1].x >= this.config.wallSpacing) {
            this.generateWall();
        }

        // Update walls
        this.walls.forEach(wall => {
            wall.x -= this.config.wallSpeed;
        });

        // Remove off-screen walls and update score
        this.walls = this.walls.filter(wall => {
            if (wall.x + wall.width < 0) {
                if (!wall.scored) {
                    this.score++;
                    wall.scored = true;
                    telemetry.debug('Score increased', { score: this.score });
                }
                return false;
            }
            return true;
        });

        // Check collisions
        this.checkCollisions();
    }

    generateWall() {
        const gapY = Math.random() * (this.height - this.config.gapSize - 100) + 50;
        
        const wall = {
            x: this.width,
            topHeight: gapY,
            bottomY: gapY + this.config.gapSize,
            bottomHeight: this.height - (gapY + this.config.gapSize),
            width: 60,
            scored: false
        };
        
        this.walls.push(wall);
        this.lastWallX = this.width;
    }

    checkCollisions() {
        // Ground and ceiling collision
        if (this.ghosty.y <= 0 || this.ghosty.y + this.ghosty.height >= this.height) {
            this.endGame('boundary');
            return;
        }

        // Wall collision
        for (let wall of this.walls) {
            if (this.ghosty.x < wall.x + wall.width &&
                this.ghosty.x + this.ghosty.width > wall.x) {
                
                if (this.ghosty.y < wall.topHeight ||
                    this.ghosty.y + this.ghosty.height > wall.bottomY) {
                    this.endGame('wall');
                    return;
                }
            }
        }
    }

    endGame(collisionType) {
        this.gameOver = true;
        this.gameRunning = false;
        telemetry.collision(collisionType, this.score);
        
        // Trigger game over event
        const event = new CustomEvent('gameOver', {
            detail: { score: this.score, difficulty: this.difficulty }
        });
        document.dispatchEvent(event);
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = '#87CEEB';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Draw Ghosty
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.fillRect(this.ghosty.x, this.ghosty.y, this.ghosty.width, this.ghosty.height);
        
        // Add simple ghost features
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(this.ghosty.x + 8, this.ghosty.y + 8, 6, 6); // Left eye
        this.ctx.fillRect(this.ghosty.x + 26, this.ghosty.y + 8, 6, 6); // Right eye

        // Draw walls
        this.ctx.fillStyle = '#228B22';
        this.walls.forEach(wall => {
            // Top wall
            this.ctx.fillRect(wall.x, 0, wall.width, wall.topHeight);
            // Bottom wall
            this.ctx.fillRect(wall.x, wall.bottomY, wall.width, wall.bottomHeight);
        });
    }

    gameLoop() {
        if (this.gameRunning) {
            this.update();
            this.render();
            requestAnimationFrame(() => this.gameLoop());
        }
    }

    getScore() {
        return this.score;
    }

    getDifficulty() {
        return this.difficulty;
    }
}