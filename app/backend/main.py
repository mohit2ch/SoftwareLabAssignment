import sys
import os
import atexit
from typing import List, Optional, Dict, Any
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError

# --- Path Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Add project root if not already there (parent of 'app' directory)
PROJECT_ROOT_CANDIDATE = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT_CANDIDATE not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_CANDIDATE)

try:
    from app.backend.proxy_scheduler import ProxyScheduler, DEFAULT_SCHEDULER_INTERVAL
    # Correctly import DEFAULT_THREADS from proxy_validator
    from app.backend.proxy_validator import DEFAULT_THREADS as DEFAULT_VALIDATION_THREADS_FROM_VALIDATOR
    from app.backend.models import ProxyItem
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print(f"Attempted PROJECT_ROOT_CANDIDATE: {PROJECT_ROOT_CANDIDATE}")
    print(f"Current sys.path: {sys.path}")
    print("Please ensure your project structure and PYTHONPATH are correct.")
    sys.exit(1)

# --- Pydantic Models for API ---
class ProxyItemResponse(BaseModel):
    ip: str
    port: int
    protocol: str
    country: Optional[str] = None
    anonymity: Optional[str] = None
    source: Optional[str] = None
    last_checked: Optional[str] = None
    response_time: Optional[float] = None
    is_valid: bool

    @classmethod
    def from_proxy_item(cls, item: ProxyItem) -> "ProxyItemResponse":
        dump_method = getattr(item, "model_dump", getattr(item, "dict", None))
        if dump_method:
            return cls(**dump_method(exclude_none=True))
        return cls(ip=item.ip, port=item.port, protocol=item.protocol, country=item.country,
                   anonymity=item.anonymity, source=item.source, last_checked=item.last_checked,
                   response_time=item.response_time, is_valid=item.is_valid)

class SchedulerStatusResponse(BaseModel):
    status: str
    validation_in_progress: bool
    interval_seconds: int
    validation_threads: int
    test_url: str
    last_run_time: Optional[str] = None
    next_run_time: Optional[str] = None
    current_proxy_count: int
    valid_proxy_count: int

class SetIntervalRequest(BaseModel):
    interval_seconds: int = Field(..., gt=0)

class SetThreadsRequest(BaseModel):
    validation_threads: int = Field(..., gt=0, le=200)

# --- Global scheduler instance ---
scheduler = ProxyScheduler(
    initial_interval_seconds=DEFAULT_SCHEDULER_INTERVAL,
    # Use the imported constant for initial_validation_threads
    initial_validation_threads=DEFAULT_VALIDATION_THREADS_FROM_VALIDATOR,
)

# --- Flask App Setup ---
app = Flask(__name__)

# CORS Setup
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:3001", "*"]}})

# --- Lifecycle / Cleanup ---
def on_startup():
    print("Flask application starting up...")
    print(f"Scheduler initial threads: {scheduler.validation_threads}, interval: {scheduler.interval_seconds}s")
    print("Scheduler is NOT auto-started. Use POST /scheduler/start to begin.")

def on_shutdown():
    print("Flask application shutting down...")
    scheduler.stop()
    print("Proxy scheduler stopped.")

# Register shutdown handler
atexit.register(on_shutdown)

# Run startup logic immediately (Flask doesn't have a built-in async lifespan like FastAPI)
on_startup()

# --- Helper: Validation Error Handler ---
def validate_body(model_class, data):
    """Validates dict data against a Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        # Return 422 to mimic FastAPI behavior
        resp = jsonify({"detail": e.errors()})
        resp.status_code = 422
        return resp

# --- API Endpoints ---

@app.route("/scheduler/start", methods=["POST"])
def start_scheduler_endpoint():
    """Start the proxy validation scheduler"""
    scheduler.start()
    return jsonify({"message": "Scheduler start initiated.", "status": scheduler.get_status()})

@app.route("/scheduler/stop", methods=["POST"])
def stop_scheduler_endpoint():
    """Stop the proxy validation scheduler"""
    scheduler.stop()
    return jsonify({"message": "Scheduler stop initiated.", "status": scheduler.get_status()})

@app.route("/scheduler/pause", methods=["POST"])
def pause_scheduler_endpoint():
    """Pause the proxy validation scheduler"""
    scheduler.pause()
    return jsonify({"message": "Scheduler pause initiated.", "status": scheduler.get_status()})

@app.route("/scheduler/resume", methods=["POST"])
def resume_scheduler_endpoint():
    """Resume a paused proxy validation scheduler"""
    scheduler.resume()
    return jsonify({"message": "Scheduler resume initiated.", "status": scheduler.get_status()})

@app.route("/scheduler/refresh", methods=["POST"])
def refresh_scheduler_endpoint():
    """Trigger an immediate proxy validation run"""
    result_message = scheduler.refresh_now(background=True)
    return jsonify({"message": result_message, "status_after_request": scheduler.get_status()})

@app.route("/scheduler/interval", methods=["POST"])
def set_scheduler_interval_endpoint():
    """Set the validation interval"""
    payload = validate_body(SetIntervalRequest, request.get_json())
    if isinstance(payload, Response): return payload # Return error if validation failed

    scheduler.set_interval(payload.interval_seconds)
    return jsonify({"message": f"Scheduler interval set to {payload.interval_seconds}s.", "status": scheduler.get_status()})

@app.route("/scheduler/threads", methods=["POST"])
def set_scheduler_threads_endpoint():
    """Set the number of validation threads"""
    payload = validate_body(SetThreadsRequest, request.get_json())
    if isinstance(payload, Response): return payload # Return error if validation failed

    scheduler.set_validation_threads(payload.validation_threads)
    return jsonify({"message": f"Validation threads set to {payload.validation_threads}.", "status": scheduler.get_status()})

@app.route("/scheduler/status", methods=["GET"])
def get_scheduler_status_endpoint():
    """Get current scheduler status"""
    current_status = scheduler.get_status()
    
    # Create Pydantic model
    response_model = SchedulerStatusResponse(
        status=current_status.get("status", "unknown"),
        validation_in_progress=current_status.get("validation_in_progress", False),
        interval_seconds=current_status.get("interval_seconds", 0),
        validation_threads=current_status.get("validation_threads", 0),
        test_url=current_status.get("test_url", ""),
        last_run_time=current_status.get("last_run_time"),
        next_run_time=current_status.get("next_run_time"),
        current_proxy_count=current_status.get("current_proxy_count", 0),
        valid_proxy_count=current_status.get("valid_proxy_count", 0)
    )
    
    # Dump to dict for JSON serialization
    return jsonify(response_model.model_dump() if hasattr(response_model, "model_dump") else response_model.dict())

@app.route("/proxies", methods=["GET"])
def get_proxies_list_endpoint():
    """Get list of proxies"""
    # Handle boolean query param manually
    only_valid_arg = request.args.get("only_valid", "true").lower()
    only_valid = only_valid_arg in ["true", "1", "yes", "on"]

    proxy_items = scheduler.get_proxies(only_valid=only_valid)
    
    # Convert to response models then to dicts
    response_list = [ProxyItemResponse.from_proxy_item(p) for p in proxy_items]
    data = [item.model_dump() if hasattr(item, "model_dump") else item.dict() for item in response_list]
    
    return jsonify(data)

# --- Main execution for Flask (for direct script run `python app/backend/main.py`) ---
if __name__ == "__main__":
    print("Starting Flask server directly from main.py script...")
    try:
        ProxyItem(ip="1.2.3.4", port=8080, protocol="http", source="test_main_script_direct_run")
        print(f"Successfully created a test ProxyItem instance.")
    except Exception as e:
        print(f"Failed to instantiate ProxyItem in __main__: {e}.")
        sys.exit(1)
    
    # Running without reloader to prevent duplicated scheduler initialization during dev
    # 'debug=True' enables the debugger. 
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=True)
