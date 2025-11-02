import os
import json
import re
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)
CORS(app)

# Setup OpenTelemetry
def setup_telemetry():
    """Setup OpenTelemetry for Kubernetes deployment"""
    
    # Set up tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure OTLP exporter for CloudWatch (via ADOT)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument Flask and requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    
    # Configure structured logging
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "flappy-kiro-backend", "message": "%(message)s", "module": "%(name)s"}'
    )
    
    return tracer

# Initialize telemetry
tracer = setup_telemetry()
logger = logging.getLogger('flappy-kiro-backend')

# Data file path
DATA_DIR = '/app/data'
SCORES_FILE = os.path.join(DATA_DIR, 'scores.json')

def load_scores():
    """Load scores from JSON file"""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                scores = json.load(f)
                logger.info(f"Loaded {len(scores)} scores from storage")
                return scores
        else:
            logger.info("No scores file found, returning empty list")
            return []
    except Exception as e:
        logger.error(f"Error loading scores: {str(e)}")
        return []

def save_scores(scores):
    """Save scores to JSON file"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
        logger.info(f"Saved {len(scores)} scores to storage")
        return True
    except Exception as e:
        logger.error(f"Error saving scores: {str(e)}")
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
    """Health check endpoint for Kubernetes"""
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("service.name", "flappy-kiro-backend")
        span.set_attribute("health.status", "healthy")
        
        # Check if data directory is writable
        try:
            test_file = os.path.join(DATA_DIR, 'health_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            storage_healthy = True
        except Exception:
            storage_healthy = False
        
        health_status = {
            'status': 'healthy' if storage_healthy else 'degraded',
            'service': 'flappy-kiro-backend',
            'storage': 'healthy' if storage_healthy else 'error',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Health check performed: {health_status['status']}")
        return jsonify(health_status), 200 if storage_healthy else 503

@app.route('/scores', methods=['POST'])
def submit_score():
    """Submit a new high score"""
    with tracer.start_as_current_span("submit_score") as span:
        try:
            data = request.get_json()
            
            if not data:
                span.set_attribute("error", "No data provided")
                logger.warning("Score submission failed: No data provided")
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate username
            username_valid, username_message = validate_username(data.get('username'))
            if not username_valid:
                span.set_attribute("error", f"Username validation failed: {username_message}")
                logger.warning(f"Score submission failed: {username_message}")
                return jsonify({'error': username_message}), 400
            
            # Validate score data
            data_valid, data_message = validate_score_data(data)
            if not data_valid:
                span.set_attribute("error", f"Data validation failed: {data_message}")
                logger.warning(f"Score submission failed: {data_message}")
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
                rank = scores.index(new_score) + 1
                span.set_attribute("username", new_score['username'])
                span.set_attribute("score", new_score['score'])
                span.set_attribute("difficulty", new_score['difficulty'])
                span.set_attribute("rank", rank)
                
                logger.info(f"Score submitted successfully: {new_score['username']} scored {new_score['score']} on {new_score['difficulty']} (rank: {rank})")
                return jsonify({'message': 'Score submitted successfully', 'rank': rank}), 201
            else:
                span.set_attribute("error", "Failed to save scores")
                logger.error("Score submission failed: Could not save to storage")
                return jsonify({'error': 'Failed to save score'}), 500
                
        except Exception as e:
            span.set_attribute("error", str(e))
            logger.error(f"Score submission error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get the global leaderboard"""
    with tracer.start_as_current_span("get_leaderboard") as span:
        try:
            scores = load_scores()
            
            # Return top 20 scores
            top_scores = scores[:20]
            
            span.set_attribute("scores_returned", len(top_scores))
            logger.info(f"Leaderboard accessed, returned {len(top_scores)} entries")
            return jsonify(top_scores), 200
            
        except Exception as e:
            span.set_attribute("error", str(e))
            logger.error(f"Leaderboard error: {str(e)}")
            return jsonify({'error': 'Failed to load leaderboard'}), 500

@app.route('/logs', methods=['POST'])
def receive_frontend_logs():
    """Receive logs from frontend for centralized logging"""
    with tracer.start_as_current_span("receive_frontend_logs") as span:
        try:
            log_data = request.get_json()
            
            if log_data:
                level = log_data.get('level', 'info').upper()
                message = log_data.get('message', '')
                data = log_data.get('data', {})
                
                span.set_attribute("frontend.level", level)
                span.set_attribute("frontend.message", message)
                
                logger.info(f"Frontend log [{level}]: {message} - {data}")
                return jsonify({'message': 'Log received'}), 200
            else:
                span.set_attribute("error", "No log data provided")
                return jsonify({'error': 'No log data provided'}), 400
                
        except Exception as e:
            span.set_attribute("error", str(e))
            logger.error(f"Frontend log processing error: {str(e)}")
            return jsonify({'error': 'Failed to process log'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get game statistics"""
    with tracer.start_as_current_span("get_stats") as span:
        try:
            scores = load_scores()
            
            if not scores:
                stats = {
                    'total_games': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'difficulty_distribution': {}
                }
            else:
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
            
            span.set_attribute("total_games", stats['total_games'])
            span.set_attribute("highest_score", stats['highest_score'])
            
            logger.info(f"Stats requested: {stats['total_games']} total games")
            return jsonify(stats), 200
            
        except Exception as e:
            span.set_attribute("error", str(e))
            logger.error(f"Stats error: {str(e)}")
            return jsonify({'error': 'Failed to calculate statistics'}), 500

if __name__ == '__main__':
    logger.info("Starting Flappy Kiro Backend Service")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"OTEL endpoint: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'not set')}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)