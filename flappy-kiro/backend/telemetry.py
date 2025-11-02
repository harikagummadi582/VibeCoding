import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def setup_telemetry(app):
    """Setup OpenTelemetry for the Flask application"""
    
    # Set up tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:14268/api/traces")
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument Flask and requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return tracer

class GameLogger:
    """Custom logger for game events with structured logging"""
    
    def __init__(self, tracer):
        self.logger = logging.getLogger('flappy-kiro-backend')
        self.tracer = tracer
    
    def log_score_submission(self, username, score, difficulty, success=True):
        """Log score submission events"""
        with self.tracer.start_as_current_span("score_submission") as span:
            span.set_attribute("username", username)
            span.set_attribute("score", score)
            span.set_attribute("difficulty", difficulty)
            span.set_attribute("success", success)
            
            if success:
                self.logger.info(f"Score submitted: {username} scored {score} on {difficulty}")
            else:
                self.logger.error(f"Score submission failed: {username}")
    
    def log_leaderboard_access(self, entries_count):
        """Log leaderboard access"""
        with self.tracer.start_as_current_span("leaderboard_access") as span:
            span.set_attribute("entries_count", entries_count)
            self.logger.info(f"Leaderboard accessed, {entries_count} entries returned")
    
    def log_frontend_event(self, event_data):
        """Log events from frontend"""
        with self.tracer.start_as_current_span("frontend_event") as span:
            span.set_attribute("service", event_data.get("service", "unknown"))
            span.set_attribute("level", event_data.get("level", "info"))
            span.set_attribute("message", event_data.get("message", ""))
            
            level = event_data.get("level", "info").upper()
            message = event_data.get("message", "")
            data = event_data.get("data", {})
            
            log_message = f"Frontend: {message} - {data}"
            
            if level == "ERROR":
                self.logger.error(log_message)
            elif level == "WARN":
                self.logger.warning(log_message)
            elif level == "DEBUG":
                self.logger.debug(log_message)
            else:
                self.logger.info(log_message)
    
    def log_api_error(self, endpoint, error_message, status_code):
        """Log API errors"""
        with self.tracer.start_as_current_span("api_error") as span:
            span.set_attribute("endpoint", endpoint)
            span.set_attribute("error_message", error_message)
            span.set_attribute("status_code", status_code)
            
            self.logger.error(f"API Error on {endpoint}: {error_message} (Status: {status_code})")
    
    def log_data_operation(self, operation, success=True, details=None):
        """Log data operations (file read/write)"""
        with self.tracer.start_as_current_span("data_operation") as span:
            span.set_attribute("operation", operation)
            span.set_attribute("success", success)
            
            if details:
                span.set_attribute("details", str(details))
            
            if success:
                self.logger.info(f"Data operation successful: {operation}")
            else:
                self.logger.error(f"Data operation failed: {operation} - {details}")