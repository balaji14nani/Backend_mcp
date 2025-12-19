# Complete Flow: Client → Server → Gemini → mcp1.py → Gemini → Client

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         COMPLETE SYSTEM FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

[1] CLIENT SENDS MESSAGE
    │
    │  POST /message
    │  { "text": "Is a 10nm carbon dot toxic?" }
    │
    ▼
┌──────────────────┐
│   test.py        │  [2] RECEIVES REQUEST
│   (FastAPI)      │      - Extracts message text
└──────────────────┘      - Initializes conversation
    │
    │  Sends message + system prompt + tools
    │
    ▼
┌──────────────────┐
│   Gemini AI      │  [3] ANALYZES MESSAGE
│   (Google)       │      - Understands intent
└──────────────────┘      - Decides to call tool
    │
    │  Returns function call request:
    │  {
    │    "name": "predict_toxicity_without_family",
    │    "args": {
    │      "ParticleSize": 10.0,
    │      "ZetaPotential": -20.0,
    │      ...
    │    }
    │  }
    │
    ▼
┌──────────────────┐
│   test.py        │  [4] EXECUTES TOOL
│   (FastAPI)      │      - Calls execute_function()
└──────────────────┘      - Passes to mcp1.py
    │
    │  execute_function(func_name, **args)
    │
    ▼
┌──────────────────┐
│   mcp1.py        │  [5] RUNS ML MODEL
│   (ML Logic)     │      - Loads PKL files
└──────────────────┘      - Makes prediction
    │                      - Calculates SHAP values
    │
    │  Returns result:
    │  {
    │    "success": True,
    │    "prediction": 0,
    │    "class_label": "NON-TOXIC",
    │    "probability_toxic": 0.244,
    │    "confidence": 0.756
    │  }
    │
    ▼
┌──────────────────┐
│   test.py        │  [6] SENDS RESULT BACK
│   (FastAPI)      │      - Formats as function response
└──────────────────┘      - Adds to conversation
    │
    │  Sends tool result back to Gemini
    │
    ▼
┌──────────────────┐
│   Gemini AI      │  [7] FORMATS RESPONSE
│   (Google)       │      - Interprets results
└──────────────────┘      - Generates natural language
    │
    │  Returns final text:
    │  "Based on the prediction, the 10nm carbon dot
    │   is NON-TOXIC with 75.6% confidence. The model
    │   considered factors like particle size, surface
    │   charge, and dose concentration..."
    │
    ▼
┌──────────────────┐
│   test.py        │  [8] RETURNS TO CLIENT
│   (FastAPI)      │      - Extracts text response
└──────────────────┘      - Includes tool call details
    │
    │  JSON Response:
    │  {
    │    "success": true,
    │    "text": "Based on the prediction...",
    │    "tool_calls": [{
    │      "function": "predict_toxicity_without_family",
    │      "result": { ... }
    │    }]
    │  }
    │
    ▼
┌──────────────────┐
│   CLIENT         │  [9] DISPLAYS RESULT
│   (Frontend)     │      - Shows AI response
└──────────────────┘      - Shows prediction details
```

## Detailed Step-by-Step

### Step 1: Client Sends Message

**Client (JavaScript):**
```javascript
fetch('http://localhost:8000/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: "Is a 10nm carbon dot toxic at 50 µg/mL?"
    })
})
```

**What happens:**
- Frontend sends natural language question
- No need to format parameters
- Gemini will extract them

---

### Step 2: test.py Receives Request

**In test.py:**
```python
@app.post("/message")
def message(msg: Message):
    # Receives: msg.text = "Is a 10nm carbon dot toxic?"
    
    conversation = [
        {"role": "user", "parts": [{"text": msg.text}]}
    ]
```

**What happens:**
- FastAPI endpoint receives request
- Initializes conversation history
- Prepares to send to Gemini

---

### Step 3: test.py → Gemini AI

**In test.py:**
```python
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=conversation,
    config={
        "tools": [toxicity_toolkit],  # Available tools
        "system_instruction": SYSTEM_PROMPT,
        "temperature": 0.1
    }
)
```

**What happens:**
- Sends message to Gemini
- Includes tool definitions
- Includes system instructions

---

### Step 4: Gemini Analyzes & Decides to Call Tool

**Gemini's decision process:**
```
Input: "Is a 10nm carbon dot toxic at 50 µg/mL?"

Analysis:
- User wants toxicity prediction
- Has ParticleSize (10nm) and Dose (50 µg/mL)
- Missing: ZetaPotential, Time, Solvent, CellType, CellOrigin
- Need to ask for missing parameters

OR (if all params provided):
- Has all required parameters
- Should call predict_toxicity_without_family
```

**Gemini returns:**
```python
{
    "function_call": {
        "name": "predict_toxicity_without_family",
        "args": {
            "ParticleSize": 10.0,
            "ZetaPotential": -20.0,
            "Dose": 50.0,
            "Time": 24,
            "Solvent": "Water",
            "CellType": "HeLa",
            "CellOrigin": "Human"
        }
    }
}
```

---

### Step 5: test.py Executes Tool via mcp1.py

**In test.py:**
```python
if part.function_call:
    func_name = part.function_call.name
    func_args = dict(part.function_call.args)
    
    # Call mcp1.py
    result = execute_function(func_name, **func_args)
```

**In mcp1.py:**
```python
def execute_function(function_name, **kwargs):
    func = AVAILABLE_FUNCTIONS[function_name]
    result = func(**kwargs)
    return result

def predict_toxicity_without_family(...):
    # Load PKL files (already loaded at import)
    # Transform features
    # Make prediction
    # Return result
```

**Result from mcp1.py:**
```python
{
    "success": True,
    "prediction": 0,
    "class_label": "NON-TOXIC",
    "probability_toxic": 0.244,
    "probability_non_toxic": 0.756,
    "confidence": 0.756,
    "model_used": "without_family"
}
```

---

### Step 6: test.py Sends Result Back to Gemini

**In test.py:**
```python
# Add function response to conversation
function_responses.append(
    Part.from_function_response(
        name=func_name,
        response=result
    )
)

# Add to conversation history
conversation.append({
    "role": "model",
    "parts": [Part.from_function_call(...)]
})
conversation.append({
    "role": "user",
    "parts": function_responses
})

# Send back to Gemini
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=conversation,  # Updated conversation
    config={...}
)
```

**What happens:**
- Tool result added to conversation
- Sent back to Gemini
- Gemini now has the prediction data

---

### Step 7: Gemini Formats Natural Language Response

**Gemini receives:**
```python
{
    "function_result": {
        "name": "predict_toxicity_without_family",
        "response": {
            "prediction": 0,
            "class_label": "NON-TOXIC",
            "probability_toxic": 0.244,
            ...
        }
    }
}
```

**Gemini generates:**
```
"Based on the model prediction, the 10nm carbon dot at 50 µg/mL 
is predicted to be NON-TOXIC with 75.6% confidence. The model 
analyzed several factors including particle size, surface charge, 
dosage concentration, and cell characteristics. The relatively 
small particle size and moderate dose suggest low toxicity risk 
for HeLa cells under these conditions.

Important: This is a computational prediction for research purposes. 
Always validate with experimental data."
```

---

### Step 8: test.py Returns to Client

**In test.py:**
```python
# Extract final text from Gemini
for candidate in response.candidates:
    for part in candidate.content.parts:
        if part.text:
            final_text = part.text

# Return to client
return {
    "success": True,
    "text": final_text,          # Gemini's natural language response
    "tool_calls": tool_results,  # Raw prediction data
    "iterations": iteration      # Number of back-and-forth rounds
}
```

---

### Step 9: Client Receives & Displays

**Client receives:**
```json
{
    "success": true,
    "text": "Based on the model prediction, the 10nm carbon dot...",
    "tool_calls": [
        {
            "function": "predict_toxicity_without_family",
            "arguments": {
                "ParticleSize": 10.0,
                "ZetaPotential": -20.0,
                ...
            },
            "result": {
                "prediction": 0,
                "class_label": "NON-TOXIC",
                "probability_toxic": 0.244,
                "confidence": 0.756
            }
        }
    ],
    "iterations": 2
}
```

**Frontend displays:**
```javascript
// Show AI response
<div className="ai-message">
    {data.text}
</div>

// Show prediction details
<div className="prediction-details">
    <span className="label non-toxic">NON-TOXIC</span>
    <span>Confidence: 75.6%</span>
</div>
```

---

## Multi-Turn Conversation Example

### Turn 1: Initial Question
```
User: "Is a 10nm carbon dot toxic?"
   ↓
Gemini: "I need more information. Please provide:
         - Dose (µg/mL)
         - Time (hours)
         - Solvent
         - Cell type
         - Cell origin"
```

### Turn 2: User Provides Details
```
User: "Dose is 50 µg/mL, 24 hours, Water solvent,
       HeLa cells, Human origin. ZetaPotential is -20mV"
   ↓
Gemini: [Calls predict_toxicity_without_family]
   ↓
mcp1.py: Returns {prediction: 0, probability_toxic: 0.244}
   ↓
Gemini: "Based on the prediction, it is NON-TOXIC with 75.6% confidence..."
```

### Turn 3: Follow-up Question
```
User: "Why is it non-toxic?"
   ↓
Gemini: [Calls explain_toxicity_prediction_without_family]
   ↓
mcp1.py: Returns {top_features: [...SHAP values...]}
   ↓
Gemini: "The main factors contributing to the non-toxic prediction are:
         1. ZetaPotential (-20mV) - decreases risk
         2. Moderate dose (50 µg/mL)
         3. Small particle size (10nm)
         ..."
```

---

## Key Files & Their Roles

| File | Role | Responsibilities |
|------|------|------------------|
| `test.py` | API Server | Receives requests, orchestrates flow |
| `mcp1.py` | ML Logic | Loads models, makes predictions |
| Gemini AI | Intelligence | Understands intent, formats responses |
| PKL files | Data | Stored models and SHAP explainers |

---

## Console Output Example

When you run `python test.py` and send a message, you'll see:

```
======================================================================
📨 [1/6] CLIENT → SERVER: Received message
======================================================================
Message: Is a 10nm carbon dot toxic at 50 µg/mL?

======================================================================
🤖 [2/6] SERVER → GEMINI: Sending message to Gemini AI
======================================================================
✓ Received response from Gemini

======================================================================
🔧 [3/6] GEMINI REQUESTED TOOL: predict_toxicity_without_family
======================================================================
Arguments: {'ParticleSize': 10.0, 'ZetaPotential': -20.0, ...}

======================================================================
⚙️  [4/6] EXECUTING: mcp1.py → predict_toxicity_without_family()
======================================================================
✓ Result: NON-TOXIC
  Probability (Toxic): 0.244

======================================================================
📤 [5/6] SERVER → GEMINI: Sending tool results back
======================================================================
Sending 1 tool result(s) to Gemini
✓ Received formatted response from Gemini

======================================================================
📨 [6/6] SERVER → CLIENT: Sending final response
======================================================================
Response: Based on the model prediction, the 10nm carbon dot at 50 µg/mL...
Tool calls executed: 1
Iterations: 2
======================================================================
```

Perfect! The complete flow is working! 🎉

