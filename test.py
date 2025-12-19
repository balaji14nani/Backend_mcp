import os
import time
from datetime import datetime, timedelta
from google import genai

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.genai.types import FunctionDeclaration, Tool, Part
from fastapi import FastAPI, Request
from mcp1 import execute_function
from collections import deque

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://chat-bot-for-machine-learning.vercel.app/"
    "https://chat-bot-for-machine-learning.vercel.app"
]

class Message(BaseModel):
    text: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

# Rate limiting tracking
request_times = deque(maxlen=15)  # Track last 15 requests
MIN_REQUEST_INTERVAL = 5.0  # Minimum 5 seconds between requests (safer for free tier)

# Model Status Caching System
MODEL_STATUS_CACHE = {
    "quota_exhausted": {},      # {model_name: timestamp_when_exhausted}
    "rate_limited": {},         # {model_name: timestamp_when_rate_limited}
    "not_found": set(),         # {model_name} - permanent failures
    "other_errors": {},         # {model_name: (error_message, timestamp)}
    "working": set(),           # {model_name} - known working models
}

# Cache expiration times (in seconds)
CACHE_EXPIRATION = {
    "quota_exhausted": 3600,    # 1 hour - quota might reset
    "rate_limited": 300,        # 5 minutes - rate limits are temporary
    "other_errors": 1800,       # 30 minutes - might be temporary
}

def is_model_cached_as_failed(model_name):
    """Check if a model is cached as failed and shouldn't be tried"""
    now = time.time()
    
    # Check permanent failures (404 not found)
    if model_name in MODEL_STATUS_CACHE["not_found"]:
        return True, "not_found"
    
    # Check quota exhausted (with expiration)
    if model_name in MODEL_STATUS_CACHE["quota_exhausted"]:
        cached_time = MODEL_STATUS_CACHE["quota_exhausted"][model_name]
        if now - cached_time < CACHE_EXPIRATION["quota_exhausted"]:
            return True, f"quota_exhausted (cached {int((now - cached_time)/60)}m ago)"
        else:
            # Expired, remove from cache
            del MODEL_STATUS_CACHE["quota_exhausted"][model_name]
    
    # Check rate limited (with expiration)
    if model_name in MODEL_STATUS_CACHE["rate_limited"]:
        cached_time = MODEL_STATUS_CACHE["rate_limited"][model_name]
        if now - cached_time < CACHE_EXPIRATION["rate_limited"]:
            return True, f"rate_limited (cached {int((now - cached_time)/60)}m ago)"
        else:
            # Expired, remove from cache
            del MODEL_STATUS_CACHE["rate_limited"][model_name]
    
    # Check other errors (with expiration)
    if model_name in MODEL_STATUS_CACHE["other_errors"]:
        error_msg, cached_time = MODEL_STATUS_CACHE["other_errors"][model_name]
        if now - cached_time < CACHE_EXPIRATION["other_errors"]:
            return True, f"other_error (cached {int((now - cached_time)/60)}m ago)"
        else:
            # Expired, remove from cache
            del MODEL_STATUS_CACHE["other_errors"][model_name]
    
    return False, None

def cache_model_failure(model_name, error_type, error_message=""):
    """Cache a model failure for future reference"""
    now = time.time()
    
    if error_type == "not_found":
        MODEL_STATUS_CACHE["not_found"].add(model_name)
        print(f"  📝 Cached {model_name} as permanently not found")
    
    elif error_type == "quota_exhausted":
        MODEL_STATUS_CACHE["quota_exhausted"][model_name] = now
        print(f"  📝 Cached {model_name} as quota exhausted (expires in {CACHE_EXPIRATION['quota_exhausted']//60}m)")
    
    elif error_type == "rate_limited":
        MODEL_STATUS_CACHE["rate_limited"][model_name] = now
        print(f"  📝 Cached {model_name} as rate limited (expires in {CACHE_EXPIRATION['rate_limited']//60}m)")
    
    elif error_type == "other_error":
        MODEL_STATUS_CACHE["other_errors"][model_name] = (error_message, now)
        print(f"  📝 Cached {model_name} as other error (expires in {CACHE_EXPIRATION['other_errors']//60}m)")

def cache_model_success(model_name):
    """Cache a model as working"""
    MODEL_STATUS_CACHE["working"].add(model_name)
    
    # Remove from failure caches if present
    MODEL_STATUS_CACHE["quota_exhausted"].pop(model_name, None)
    MODEL_STATUS_CACHE["rate_limited"].pop(model_name, None)
    MODEL_STATUS_CACHE["other_errors"].pop(model_name, None)
    
    print(f"  📝 Cached {model_name} as working")

def print_cache_status():
    """Print current cache status for debugging"""
    print(f"\n📊 Model Cache Status:")
    print(f"  🟢 Working: {len(MODEL_STATUS_CACHE['working'])} models")
    print(f"  🔴 Quota Exhausted: {len(MODEL_STATUS_CACHE['quota_exhausted'])} models")
    print(f"  🟡 Rate Limited: {len(MODEL_STATUS_CACHE['rate_limited'])} models")
    print(f"  ❌ Not Found: {len(MODEL_STATUS_CACHE['not_found'])} models")
    print(f"  ⚠️  Other Errors: {len(MODEL_STATUS_CACHE['other_errors'])} models")

# Discover available models on startup
AVAILABLE_MODELS = []
try:
    print("\n" + "="*70)
    print("Discovering available Gemini models...")
    print("="*70)
    for model in client.models.list():
        model_name = model.name
        # Extract short name (e.g., "gemini-1.5-flash" from "models/gemini-1.5-flash-001")
        short_name = model_name.split("/")[-1].split("-")[:-1]  # Remove version number
        short_name = "-".join(short_name)
        AVAILABLE_MODELS.append({
            "full_name": model_name,
            "short_name": short_name,
            "display_name": model_name.split("/")[-1]
        })
        print(f"  ✓ {model_name.split('/')[-1]}")
    
    # Set default models based on availability
    PRIMARY_MODEL = None
    FALLBACK_MODEL = None
    
    # Try to find working models in priority order
    priority_models = [
        "gemini-2.5-flash",      # This one works!
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-exp"
    ]
    
    # Find primary model
    for priority in priority_models:
        for m in AVAILABLE_MODELS:
            if priority in m["display_name"].lower():
                PRIMARY_MODEL = m["full_name"]
                break
        if PRIMARY_MODEL:
            break
    
    # Find fallback models (different from primary)
    fallback_candidates = [
        "gemini-2.0-flash",
        "gemini-2.5-pro", 
        "gemini-2.0-flash-001",
        "gemini-flash-latest",
        "gemini-pro-latest"
    ]
    
    for candidate in fallback_candidates:
        for m in AVAILABLE_MODELS:
            if candidate in m["display_name"].lower() and m["full_name"] != PRIMARY_MODEL:
                FALLBACK_MODEL = m["full_name"]
                break
        if FALLBACK_MODEL:
            break
    
    # Defaults if nothing found (use working model we discovered)
    if not PRIMARY_MODEL:
        PRIMARY_MODEL = "models/gemini-2.5-flash"
    if not FALLBACK_MODEL:
        FALLBACK_MODEL = "models/gemini-2.0-flash"
    
    print(f"\n✓ Primary model: {PRIMARY_MODEL.split('/')[-1]}")
    print(f"✓ Fallback model: {FALLBACK_MODEL.split('/')[-1]}")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"⚠️  Could not list models: {e}")
    print("Using working model names...")
    PRIMARY_MODEL = "models/gemini-2.5-flash"  # This one works!
    FALLBACK_MODEL = "models/gemini-2.0-flash"

SYSTEM_PROMPT = """
You are a toxicity prediction AI assistant specializing in carbon dot nanoparticles.

Your Role:
- Analyze carbon dot toxicity based on particle properties and cell characteristics
- Use machine learning models to make predictions
- Explain predictions using SHAP (Explainable AI) values
- Provide clear, scientific explanations

Rules:
1. ALWAYS use the prediction tools - NEVER guess or estimate
2. When user provides parameters, call the appropriate prediction function
3. After prediction, explain what factors contributed most to the result
4. If key parameters are missing, ask the user for them
5. Be precise about confidence levels and uncertainties
6. Add disclaimers: These are computational predictions for research purposes

Available Tools:
- predict_toxicity_without_family: For predictions when plant family is unknown
- predict_toxicity_with_family: For predictions when plant family is known
- explain_toxicity_prediction_without_family: Get detailed SHAP explanation (no family)
- explain_toxicity_prediction_with_family: Get detailed SHAP explanation (with family)

Required Parameters:
- ParticleSize (nm): Particle diameter
- ZetaPotential (mV): Surface charge
- Dose (µg/mL): Concentration
- Time (hours): Exposure duration
- Solvent: Extraction solvent (Ethanol, Water, etc.)
- CellType: Cell line tested (HeLa, MCF7, etc.)
- CellOrigin: Species (Human, Mouse, Rat)
- Family (optional): Plant family name

Example Interaction:
User: "Is a 10nm carbon dot toxic at 50 µg/mL for 24h?"
You: Ask for missing parameters (Solvent, CellType, etc.)
User: Provides parameters
You: Call prediction tool → Get result → Explain using SHAP values
"""

# Tool declarations
predict_without_family = FunctionDeclaration(
    name="predict_toxicity_without_family",
    description="Predict carbon dot toxicity without plant family information. Returns prediction (0=non-toxic, 1=toxic), probability scores, and confidence level.",
    parameters={
        "type": "object",
        "properties": {
            "ParticleSize": {
                "type": "number",
                "description": "Carbon dot particle size in nanometers (e.g., 7.5)"
            },
            "ZetaPotential": {
                "type": "number",
                "description": "Surface charge in millivolts (e.g., -22.0, typically negative)"
            },
            "Dose": {
                "type": "number",
                "description": "Dosage concentration in µg/mL (e.g., 15.0)"
            },
            "Time": {
                "type": "number",
                "description": "Exposure time in hours (e.g., 24, 48, 72)"
            },
            "Solvent": {
                "type": "string",
                "description": "Extraction solvent used (e.g., 'Ethanol', 'Water', 'Methanol', 'DMSO')"
            },
            "CellType": {
                "type": "string",
                "description": "Cell type/line tested (e.g., 'HeLa', 'MCF7', 'A549', 'NIH3T3')"
            },
            "CellOrigin": {
                "type": "string",
                "description": "Organism origin of cells (e.g., 'Human', 'Mouse', 'Rat')"
            },
        },
        "required": [
            "ParticleSize", "ZetaPotential", "Dose",
            "Time", "Solvent", "CellType", "CellOrigin"
        ]
    }
)

predict_with_family = FunctionDeclaration(
    name="predict_toxicity_with_family",
    description="Predict carbon dot toxicity with plant family information. Use this when the carbon dots are derived from plant material and you know the plant family.",
    parameters={
        "type": "object",
        "properties": {
            "ParticleSize": {
                "type": "number",
                "description": "Carbon dot particle size in nanometers"
            },
            "ZetaPotential": {
                "type": "number",
                "description": "Surface charge in millivolts"
            },
            "Dose": {
                "type": "number",
                "description": "Dosage concentration in µg/mL"
            },
            "Time": {
                "type": "number",
                "description": "Exposure time in hours"
            },
            "Family": {
                "type": "string",
                "description": "Plant family name (e.g., 'Fabaceae', 'Rosaceae', 'Moraceae')"
            },
            "Solvent": {
                "type": "string",
                "description": "Extraction solvent used"
            },
            "CellType": {
                "type": "string",
                "description": "Cell type tested"
            },
            "CellOrigin": {
                "type": "string",
                "description": "Organism origin (Human/Mouse/Rat)"
            },
        },
        "required": [
            "ParticleSize", "ZetaPotential", "Dose",
            "Time", "Family", "Solvent", "CellType", "CellOrigin"
        ]
    }
)

explain_without_family = FunctionDeclaration(
    name="explain_toxicity_prediction_without_family",
    description="Explain toxicity prediction using SHAP (Explainable AI) without plant family. Returns detailed explanation of which features contributed most to the prediction and how.",
    parameters={
        "type": "object",
        "properties": {
            "ParticleSize": {"type": "number"},
            "ZetaPotential": {"type": "number"},
            "Dose": {"type": "number"},
            "Time": {"type": "number"},
            "Solvent": {"type": "string"},
            "CellType": {"type": "string"},
            "CellOrigin": {"type": "string"},
            "top_n": {
                "type": "integer",
                "description": "Number of top SHAP features to return (default: 10)"
            },
            "save_plot": {
                "type": "boolean",
                "description": "Whether to save waterfall plot (default: false)"
            },
        },
        "required": [
            "ParticleSize", "ZetaPotential", "Dose",
            "Time", "Solvent", "CellType", "CellOrigin"
        ]
    }
)

explain_with_family = FunctionDeclaration(
    name="explain_toxicity_prediction_with_family",
    description="Explain toxicity prediction using SHAP with plant family information. Provides detailed breakdown of feature contributions including plant family effects.",
    parameters={
        "type": "object",
        "properties": {
            "ParticleSize": {"type": "number"},
            "ZetaPotential": {"type": "number"},
            "Dose": {"type": "number"},
            "Time": {"type": "number"},
            "Family": {"type": "string"},
            "Solvent": {"type": "string"},
            "CellType": {"type": "string"},
            "CellOrigin": {"type": "string"},
            "top_n": {
                "type": "integer",
                "description": "Number of top features (default: 10)"
            },
            "save_plot": {
                "type": "boolean",
                "description": "Save explanation plot (default: false)"
            },
        },
        "required": [
            "ParticleSize", "ZetaPotential", "Dose",
            "Time", "Family", "Solvent", "CellType", "CellOrigin"
        ]
    }
)

toxicity_toolkit = Tool(
    function_declarations=[
        predict_without_family,
        predict_with_family,
        explain_without_family,
        explain_with_family,
    ]
)


def throttle_requests():
    """Throttle requests to respect rate limits"""
    global request_times
    
    now = time.time()
    
    # Remove requests older than 1 minute
    while request_times and now - request_times[0] > 60:
        request_times.popleft()
    
    # If we have recent requests, wait
    if request_times:
        time_since_last = now - request_times[-1]
        if time_since_last < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - time_since_last
            print(f"⏳ Throttling: Waiting {wait_time:.1f}s to respect rate limits...")
            time.sleep(wait_time)
    
    # Record this request
    request_times.append(time.time())


def call_gemini_with_model_iteration(contents, config):
    """
    Call Gemini API by iterating through all available models until one works.
    Uses intelligent caching to skip models that are known to be failing.
    
    Parameters:
    -----------
    contents : list
        Conversation contents
    config : dict
        Generation config
    
    Returns:
    --------
    tuple: (Response from Gemini API, model_used) or (None, None) if all fail
    """
    # Create priority list of models to try
    models_to_try = []
    
    # Prioritize known working models first
    working_models = list(MODEL_STATUS_CACHE["working"])
    
    # Add primary model first (if not already in working set)
    if PRIMARY_MODEL and PRIMARY_MODEL not in working_models:
        models_to_try.append(PRIMARY_MODEL)
    
    # Add known working models next
    models_to_try.extend(working_models)
    
    # Add fallback model
    if FALLBACK_MODEL and FALLBACK_MODEL not in models_to_try:
        models_to_try.append(FALLBACK_MODEL)
    
    # Add all other available models (excluding ones already added)
    for model_info in AVAILABLE_MODELS:
        model_name = model_info["full_name"]
        if model_name not in models_to_try:
            # Only add text generation models (skip embedding, image, etc.)
            display_name = model_info["display_name"].lower()
            if any(keyword in display_name for keyword in ["gemini", "gemma"]) and \
               not any(skip in display_name for skip in ["embedding", "imagen", "veo", "tts", "audio"]):
                models_to_try.append(model_name)
    
    # Filter out cached failed models
    models_to_try_filtered = []
    skipped_models = []
    
    for model in models_to_try:
        is_failed, reason = is_model_cached_as_failed(model)
        if is_failed:
            skipped_models.append((model, reason))
        else:
            models_to_try_filtered.append(model)
    
    models_to_try = models_to_try_filtered
    
    # Print summary
    print(f"\n🔄 Model Selection Summary:")
    print(f"  ✅ Available to try: {len(models_to_try)} models")
    print(f"  ⏭️  Skipped (cached failures): {len(skipped_models)} models")
    
    if skipped_models:
        print(f"\n⏭️  Skipping cached failed models:")
        for model, reason in skipped_models[:5]:  # Show first 5
            print(f"    • {model.split('/')[-1]}: {reason}")
        if len(skipped_models) > 5:
            print(f"    ... and {len(skipped_models) - 5} more")
    
    print(f"\n🔄 Will try {len(models_to_try)} models in order:")
    for i, model in enumerate(models_to_try[:5], 1):  # Show first 5
        marker = "🟢" if model in MODEL_STATUS_CACHE["working"] else "🔵"
        print(f"  {marker} {i}. {model.split('/')[-1]}")
    if len(models_to_try) > 5:
        print(f"  ... and {len(models_to_try) - 5} more")
    
    if not models_to_try:
        print(f"\n❌ No models available to try (all cached as failed)")
        print_cache_status()
        return None, None
    
    # Try each model
    models_tried = 0
    for model_index, model in enumerate(models_to_try, 1):
        try:
            print(f"\n🤖 [{model_index}/{len(models_to_try)}] Trying: {model.split('/')[-1]}")
            models_tried += 1
            
            # Throttle before making request
            throttle_requests()
            
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            print(f"✅ SUCCESS with {model.split('/')[-1]}!")
            
            # Cache this model as working
            cache_model_success(model)
            
            return response, model
            
        except Exception as e:
            error_str = str(e)
            
            # Check error type
            is_rate_limit = any(indicator in error_str.lower() for indicator in [
                "429", "resource_exhausted", "quota", "rate limit", "too many requests"
            ])
            is_not_found = any(indicator in error_str.lower() for indicator in [
                "404", "not_found", "not found", "is not found"
            ])
            is_quota_exhausted = "limit: 0" in error_str.lower()
            
            # Handle and cache different error types
            if is_not_found:
                print(f"  ❌ Model not found (404)")
                cache_model_failure(model, "not_found")
            
            elif is_quota_exhausted:
                print(f"  ❌ Quota exhausted (limit: 0)")
                cache_model_failure(model, "quota_exhausted")
            
            elif is_rate_limit:
                print(f"  ⚠️  Rate limited")
                cache_model_failure(model, "rate_limited")
                # For rate limits, wait a bit before trying next model
                if model_index < len(models_to_try):
                    print(f"  ⏳ Waiting 10s before trying next model...")
                    time.sleep(10)
            
            else:
                print(f"  ❌ Other error: {error_str[:100]}")
                cache_model_failure(model, "other_error", error_str[:200])
            
            # Continue to next model
            continue
    
    # All models failed
    print(f"\n❌ All {models_tried} available models failed!")
    print(f"   (Skipped {len(skipped_models)} cached failed models)")
    print_cache_status()
    
    print("\n💡 Possible solutions:")
    print("   1. Wait a few minutes for quota reset")
    print("   2. Check quota at: https://ai.dev/usage")
    print("   3. Try again later")
    
    return None, None


@app.post("/message")
def message(msg: Message):
    """
    Complete flow:
    1. Client sends message → test.py
    2. test.py sends to Gemini
    3. Gemini calls tools → test.py executes via mcp1.py
    4. test.py sends results back to Gemini
    5. Gemini generates natural language response
    6. test.py returns final response to client
    """
    try:
        print("\n" + "="*70)
        print("📨 [1/6] CLIENT → SERVER: Received message")
        print("="*70)
        print(f"Message: {msg.text[:100]}...")
        
        # Initialize conversation history
        conversation = [
            {
                "role": "user",
                "parts": [{"text": msg.text}]
            }
        ]
        
        print("\n" + "="*70)
        print("🤖 [2/6] SERVER → GEMINI: Sending message to Gemini AI")
        print("="*70)
        
        # Will try all available models automatically
        
        # Try all available models until one works
        response, model_used = call_gemini_with_model_iteration(
            contents=conversation,
            config={
                "tools": [toxicity_toolkit],
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.1,
            }
        )
        
        if response is None:
            raise Exception("❌ No available models could handle the request. All models failed.")
        
        print(f"✓ Using model: {model_used.split('/')[-1]}")
        model_to_use = model_used
        
        # Store model for later use in the loop
        current_model = model_used
        
        # Process response and execute tool calls
        max_iterations = 3  # Prevent infinite loops
        iteration = 0
        final_text = ""
        tool_results = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check if there are function calls
            has_function_call = False
            function_responses = []
            
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.text:
                        final_text = part.text
                    
                    if part.function_call:
                        has_function_call = True
                        func_name = part.function_call.name
                        func_args = dict(part.function_call.args)
                        
                        print("\n" + "="*70)
                        print(f"🔧 [3/6] GEMINI REQUESTED TOOL: {func_name}")
                        print("="*70)
                        print(f"Arguments: {func_args}")
                        
                        print("\n" + "="*70)
                        print(f"⚙️  [4/6] EXECUTING: mcp1.py → {func_name}()")
                        print("="*70)
                        
                        # Execute the tool using mcp1.py
                        result = execute_function(func_name, **func_args)
                        
                        if result.get("success"):
                            print(f"✓ Result: {result.get('class_label', 'N/A')}")
                            if 'probability_toxic' in result:
                                print(f"  Probability (Toxic): {result['probability_toxic']:.3f}")
                        else:
                            print(f"✗ Error: {result.get('error', 'Unknown')}")
                        
                        tool_results.append({
                            "function": func_name,
                            "arguments": func_args,
                            "result": result
                        })
                        
                        # Add function response to conversation
                        function_responses.append(
                            Part.from_function_response(
                                name=func_name,
                                response=result
                            )
                        )
            
            # If no function calls, we're done
            if not has_function_call:
                break
            
            # Add function responses to conversation and continue
            conversation.append({
                "role": "model",
                "parts": [Part.from_function_call(
                    name=call["function"],
                    args=call["arguments"]
                ) for call in tool_results[-len(function_responses):]]
            })
            
            conversation.append({
                "role": "user",
                "parts": function_responses
            })
            
            print("\n" + "="*70)
            print("📤 [5/6] SERVER → GEMINI: Sending tool results back")
            print("="*70)
            print(f"Sending {len(function_responses)} tool result(s) to Gemini")
            
            # Get next response - try all models until one works
            response, model_used = call_gemini_with_model_iteration(
                contents=conversation,
                config={
                    "tools": [toxicity_toolkit],
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.1,
                }
            )
            
            if response is None:
                print(f"\n❌ No available models could handle the follow-up request")
                break  # Exit the loop, return what we have so far
            
            print(f"✓ Follow-up response from: {model_used.split('/')[-1]}")
            current_model = model_used
        
        # Extract final text
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.text:
                    final_text = part.text
        
        print("\n" + "="*70)
        print("📨 [6/6] SERVER → CLIENT: Sending final response")
        print("="*70)
        print(f"Response: {final_text[:150]}...")
        print(f"Tool calls executed: {len(tool_results)}")
        print(f"Iterations: {iteration}")
        print("="*70 + "\n")
        
        return {
            "success": True,
            "text": final_text,
            "tool_calls": tool_results,
            "iterations": iteration
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "text": f"Error: {str(e)}",
            "error_details": traceback.format_exc(),
            "tool_calls": []
        }


def reset_model_cache():
    """Reset the model status cache"""
    global MODEL_STATUS_CACHE
    MODEL_STATUS_CACHE = {
        "quota_exhausted": {},
        "rate_limited": {},
        "not_found": set(),
        "other_errors": {},
        "working": set(),
    }
    print("🔄 Model cache reset!")

@app.get("/health")
def health_check():
    """Health check endpoint with cache status"""
    return {
        "status": "healthy",
        "models_loaded": True,
        "tools_available": [
            "predict_toxicity_without_family",
            "predict_toxicity_with_family",
            "explain_toxicity_prediction_without_family",
            "explain_toxicity_prediction_with_family"
        ],
        "cache_status": {
            "working_models": len(MODEL_STATUS_CACHE["working"]),
            "quota_exhausted": len(MODEL_STATUS_CACHE["quota_exhausted"]),
            "rate_limited": len(MODEL_STATUS_CACHE["rate_limited"]),
            "not_found": len(MODEL_STATUS_CACHE["not_found"]),
            "other_errors": len(MODEL_STATUS_CACHE["other_errors"]),
        },
        "primary_model": PRIMARY_MODEL.split('/')[-1] if PRIMARY_MODEL else None,
        "fallback_model": FALLBACK_MODEL.split('/')[-1] if FALLBACK_MODEL else None,
    }

@app.get("/cache/status")
def get_cache_status():
    """Get detailed cache status"""
    now = time.time()
    
    # Get detailed info with expiration times
    detailed_status = {
        "working_models": list(MODEL_STATUS_CACHE["working"]),
        "quota_exhausted": {
            model: {
                "cached_at": timestamp,
                "expires_in_minutes": max(0, int((timestamp + CACHE_EXPIRATION["quota_exhausted"] - now) / 60))
            }
            for model, timestamp in MODEL_STATUS_CACHE["quota_exhausted"].items()
        },
        "rate_limited": {
            model: {
                "cached_at": timestamp,
                "expires_in_minutes": max(0, int((timestamp + CACHE_EXPIRATION["rate_limited"] - now) / 60))
            }
            for model, timestamp in MODEL_STATUS_CACHE["rate_limited"].items()
        },
        "not_found": list(MODEL_STATUS_CACHE["not_found"]),
        "other_errors": {
            model: {
                "error": error_msg,
                "cached_at": timestamp,
                "expires_in_minutes": max(0, int((timestamp + CACHE_EXPIRATION["other_errors"] - now) / 60))
            }
            for model, (error_msg, timestamp) in MODEL_STATUS_CACHE["other_errors"].items()
        },
        "cache_expiration_settings": CACHE_EXPIRATION,
    }
    
    return detailed_status

@app.post("/cache/reset")
def reset_cache():
    """Reset the model cache"""
    reset_model_cache()
    return {"message": "Model cache reset successfully", "status": "success"}

@app.post("/cache/clear/{cache_type}")
def clear_specific_cache(cache_type: str):
    """Clear a specific type of cache"""
    if cache_type not in MODEL_STATUS_CACHE:
        return {"error": f"Invalid cache type. Available: {list(MODEL_STATUS_CACHE.keys())}", "status": "error"}
    
    if cache_type in ["quota_exhausted", "rate_limited", "other_errors"]:
        MODEL_STATUS_CACHE[cache_type].clear()
    elif cache_type in ["not_found", "working"]:
        MODEL_STATUS_CACHE[cache_type].clear()
    
    return {"message": f"Cleared {cache_type} cache", "status": "success"}


if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment variables (for deployment)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("Starting Toxicity Prediction API...")
    print("Models loaded successfully!")
    print(f"API available at: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    
    uvicorn.run(app, host=host, port=port)
