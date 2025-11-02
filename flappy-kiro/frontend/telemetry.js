// Simple telemetry for frontend logging
class Telemetry {
    constructor() {
        this.serviceName = 'flappy-kiro-frontend';
        this.logs = [];
    }

    log(level, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            service: this.serviceName,
            level: level,
            message: message,
            data: data,
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        this.logs.push(logEntry);
        console.log(`[${level.toUpperCase()}] ${message}`, data);
        
        // Send to backend for centralized logging
        this.sendLog(logEntry);
    }

    async sendLog(logEntry) {
        try {
            await fetch('http://localhost:8000/logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(logEntry)
            });
        } catch (error) {
            console.error('Failed to send log to backend:', error);
        }
    }

    info(message, data) {
        this.log('info', message, data);
    }

    warn(message, data) {
        this.log('warn', message, data);
    }

    error(message, data) {
        this.log('error', message, data);
    }

    debug(message, data) {
        this.log('debug', message, data);
    }

    // Game-specific telemetry
    gameStart(difficulty) {
        this.info('Game started', { difficulty });
    }

    gameEnd(score, difficulty) {
        this.info('Game ended', { score, difficulty });
    }

    scoreSubmitted(username, score, difficulty) {
        this.info('Score submitted', { username, score, difficulty });
    }

    collision(obstacleType, score) {
        this.info('Collision detected', { obstacleType, score });
    }
}

// Global telemetry instance
window.telemetry = new Telemetry();