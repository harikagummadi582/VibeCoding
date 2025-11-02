import os
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Data file path
DATA_DIR = './data'
SCORES_FILE = os.path.join(DATA_DIR, 'scores.json')

def load_scores():
    """Load scores from JSON file"""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                scores = json.load(f)
                print(f"Loaded {len(scores)} scores")
                return scores
        else:
            print("No scores file found, returning empty list")
            return []
    except Exception as e:
        print(f"Error loading scores: {e}")
        return []

def save_scores(scores):
    """Save scores to JSON file"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
        print(f"Saved {len(scores)} scores")
        return True
    except Exception as e:
        print(f"Error saving scores: {e}")
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
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate username
        username_valid, username_message = validate_username(data.get('username'))
        if not username_valid:
            return jsonify({'error': username_message}), 400
        
        # Validate score data
        data_valid, data_message = validate_score_data(data)
        if not data_valid:
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
            print(f"Score submitted: {new_score['username']} scored {new_score['score']} on {new_score['difficulty']}")
            return jsonify({'message': 'Score submitted successfully', 'rank': scores.index(new_score) + 1}), 201
        else:
            return jsonify({'error': 'Failed to save score'}), 500
            
    except Exception as e:
        print(f"Error in submit_score: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the global leaderboard"""
    try:
        scores = load_scores()
        
        # Return top 20 scores
        top_scores = scores[:20]
        
        print(f"Leaderboard accessed, {len(top_scores)} entries returned")
        return jsonify(top_scores), 200
        
    except Exception as e:
        print(f"Error in get_leaderboard: {e}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500

@app.route('/logs', methods=['POST'])
def receive_frontend_logs():
    """Receive logs from frontend for centralized logging"""
    try:
        log_data = request.get_json()
        
        if log_data:
            level = log_data.get('level', 'info').upper()
            message = log_data.get('message', '')
            data = log_data.get('data', {})
            
            print(f"Frontend [{level}]: {message} - {data}")
            return jsonify({'message': 'Log received'}), 200
        else:
            return jsonify({'error': 'No log data provided'}), 400
            
    except Exception as e:
        print(f"Error in receive_frontend_logs: {e}")
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
        print(f"Error in get_stats: {e}")
        return jsonify({'error': 'Failed to calculate statistics'}), 500

if __name__ == '__main__':
    print("🎮 Starting Flappy Kiro Backend...")
    print("🔧 API will be available at: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)