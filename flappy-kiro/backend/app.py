import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from telemetry import setup_telemetry, GameLogger

app = Flask(__name__)
CORS(app)

# Setup telemetry
tracer = setup_telemetry(app)
game_logger = GameLogger(tracer)

# Data file path
DATA_DIR = '/app/data'
SCORES_FILE = os.path.join(DATA_DIR, 'scores.json')

def load_scores():
    """Load scores from JSON file"""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                scores = json.load(f)
                game_logger.log_data_operation("load_scores", success=True, details=f"Loaded {len(scores)} scores")
                return scores
        else:
            game_logger.log_data_operation("load_scores", success=True, details="No scores file found, returning empty list")
            return []
    except Exception as e:
        game_logger.log_data_operation("load_scores", success=False, details=str(e))
        return []

def save_scores(scores):
    """Save scores to JSON file"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
        game_logger.log_data_operation("save_scores", success=True, details=f"Saved {len(scores)} scores")
        return True
    except Exception as e:
        game_logger.log_data_operation("save_scores", success=False, details=str(e))
        return False

def validate_username(username):
    """Validate username according to rules"""
    if not username or len(username) < 1 or len(username) > 20:
        return False, "Username must be 1-20 characters long"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Check for inappropriate content
    inappropriate_words = ['admin', 'root', 'test', 'null', 'undefined', 'bot', 'system']
    username_lower = username.lower()
    
    for word in inappropriate_words:
        if word in username_lower:
            return False, f"Username cannot contain '{word}'"
    
    return True, "Valid username"

def validate_score_data(data):
    """Validate score submission data"""
    required_fields = ['username', 'score', 'difficulty']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate score
    try:
        score = int(data['score'])
        if score < 0 or score > 10000:  # Reasonable score limits
            return False, "Score must be between 0 and 10000"
    except (ValueError, TypeError):
        return False, "Score must be a valid integer"
    
    # Validate difficulty
    valid_difficulties = ['easy', 'medium', 'hard']
    if data['difficulty'] not in valid_difficulties:
        return False, f"Difficulty must be one of: {', '.join(valid_difficulties)}"
    
    return True, "Valid score data"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'flappy-kiro-backend'}), 200

@app.route('/scores', methods=['POST'])
def submit_score():
    """Submit a new high score"""
    try:
        data = request.get_json()
        
        if not data:
            game_logger.log_api_error('/scores', 'No JSON data provided', 400)
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate username
        username_valid, username_message = validate_username(data.get('username'))
        if not username_valid:
            game_logger.log_score_submission(data.get('username', 'unknown'), 
                                           data.get('score', 0), 
                                           data.get('difficulty', 'unknown'), 
                                           success=False)
            return jsonify({'error': username_message}), 400
        
        # Validate score data
        data_valid, data_message = validate_score_data(data)
        if not data_valid:
            game_logger.log_score_submission(data.get('username', 'unknown'), 
                                           data.get('score', 0), 
                                           data.get('difficulty', 'unknown'), 
                                           success=False)
            return jsonify({'error': data_message}), 400
        
        # Load existing scores
        scores = load_scores()
        
        # Create new score entry
        new_score = {
            'username': data['username'],
            'score': int(data['score']),
            'difficulty': data['difficulty'],
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat())
        }
        
        # Add to scores list
        scores.append(new_score)
        
        # Sort by score (descending) and keep top 100
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores = scores[:100]
        
        # Save scores
        if save_scores(scores):
            game_logger.log_score_submission(new_score['username'], 
                                           new_score['score'], 
                                           new_score['difficulty'], 
                                           success=True)
            return jsonify({'message': 'Score submitted successfully', 'rank': scores.index(new_score) + 1}), 201
        else:
            game_logger.log_api_error('/scores', 'Failed to save scores', 500)
            return jsonify({'error': 'Failed to save score'}), 500
            
    except Exception as e:
        game_logger.log_api_error('/scores', str(e), 500)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the global leaderboard"""
    try:
        scores = load_scores()
        
        # Return top 20 scores
        top_scores = scores[:20]
        
        game_logger.log_leaderboard_access(len(top_scores))
        return jsonify(top_scores), 200
        
    except Exception as e:
        game_logger.log_api_error('/leaderboard', str(e), 500)
        return jsonify({'error': 'Failed to load leaderboard'}), 500

@app.route('/logs', methods=['POST'])
def receive_frontend_logs():
    """Receive logs from frontend for centralized logging"""
    try:
        log_data = request.get_json()
        
        if log_data:
            game_logger.log_frontend_event(log_data)
            return jsonify({'message': 'Log received'}), 200
        else:
            return jsonify({'error': 'No log data provided'}), 400
            
    except Exception as e:
        game_logger.log_api_error('/logs', str(e), 500)
        return jsonify({'error': 'Failed to process log'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get game statistics"""
    try:
        scores = load_scores()
        
        if not scores:
            return jsonify({
                'total_games': 0,
                'average_score': 0,
                'highest_score': 0,
                'difficulty_distribution': {}
            }), 200
        
        # Calculate statistics
        total_games = len(scores)
        average_score = sum(score['score'] for score in scores) / total_games
        highest_score = max(score['score'] for score in scores)
        
        # Difficulty distribution
        difficulty_dist = {}
        for score in scores:
            diff = score['difficulty']
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
        
        stats = {
            'total_games': total_games,
            'average_score': round(average_score, 2),
            'highest_score': highest_score,
            'difficulty_distribution': difficulty_dist
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        game_logger.log_api_error('/stats', str(e), 500)
        return jsonify({'error': 'Failed to calculate statistics'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)