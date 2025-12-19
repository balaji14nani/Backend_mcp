# Quick Reference: Complete Flow

## The Flow (Simple Version)

```
CLIENT
  ↓ (POST /message)
test.py
  ↓ (sends to AI)
GEMINI
  ↓ (decides to call tool)
test.py
  ↓ (execute_function)
mcp1.py
  ↓ (returns result)
test.py
  ↓ (sends result back)
GEMINI
  ↓ (formats response)
test.py
  ↓ (returns JSON)
CLIENT
```

## Test the Complete Flow

### Terminal 1: Start Server
```bash
cd Backend
python test.py
```

### Terminal 2: Send Request
```bash
python test_client.py
```

### Or use curl:
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Is a 10nm carbon dot toxic at 50 µg/mL for 24h? ZetaPotential: -20mV, Solvent: Water, CellType: HeLa, CellOrigin: Human"}'
```

## What You'll See

### In Server Console:
```
📨 [1/6] CLIENT → SERVER: Received message
🤖 [2/6] SERVER → GEMINI: Sending message to Gemini AI
🔧 [3/6] GEMINI REQUESTED TOOL: predict_toxicity_without_family
⚙️  [4/6] EXECUTING: mcp1.py → predict_toxicity_without_family()
✓ Result: NON-TOXIC
📤 [5/6] SERVER → GEMINI: Sending tool results back
📨 [6/6] SERVER → CLIENT: Sending final response
```

### In Client:
```json
{
  "success": true,
  "text": "Based on the prediction, the carbon dot is NON-TOXIC...",
  "tool_calls": [{
    "function": "predict_toxicity_without_family",
    "result": {
      "prediction": 0,
      "class_label": "NON-TOXIC",
      "probability_toxic": 0.244
    }
  }]
}
```

## Files & Their Jobs

| File | What It Does |
|------|--------------|
| `test.py` | Receives requests, talks to Gemini, calls mcp1.py |
| `mcp1.py` | Runs ML models, makes predictions |
| `*.pkl` | Stored models (loaded once at startup) |

## How to Use from Frontend

```javascript
// JavaScript/React
const response = await fetch('http://localhost:8000/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: "Is a 10nm carbon dot toxic?"
    })
});

const data = await response.json();

// Display AI response
console.log(data.text);

// Get raw prediction
console.log(data.tool_calls[0].result.class_label);  // "NON-TOXIC"
console.log(data.tool_calls[0].result.probability_toxic);  // 0.244
```

## Conversation Examples

### Example 1: Missing Parameters
```
User → "Is a 10nm carbon dot toxic?"
AI → "I need more information: Dose, Time, Solvent, CellType, CellOrigin"
```

### Example 2: Complete Request
```
User → "Is a 10nm carbon dot toxic at 50 µg/mL for 24h? 
        ZetaPotential: -20mV, Solvent: Water, 
        CellType: HeLa, CellOrigin: Human"

[Tool Call] → mcp1.py.predict_toxicity_without_family()

AI → "Based on the prediction, the carbon dot is NON-TOXIC 
      with 75.6% confidence. The model analyzed particle size, 
      surface charge, dose, and cell characteristics..."
```

### Example 3: Ask for Explanation
```
User → "Why is it non-toxic?"

[Tool Call] → mcp1.py.explain_toxicity_prediction_without_family()

AI → "The main factors contributing to this prediction are:
      1. ZetaPotential (-20mV) - decreases toxicity risk
      2. Moderate dose (50 µg/mL)
      3. Small particle size (10nm)
      ..."
```

## Key Features

✅ **Natural Language** - Just ask questions, no need to format JSON  
✅ **Auto Tool Calling** - Gemini decides when to use ML models  
✅ **Multi-Turn** - Can have back-and-forth conversations  
✅ **SHAP Explanations** - Explainable AI built-in  
✅ **Error Handling** - Graceful failures with helpful messages  

## Troubleshooting

### "Models not loading"
```bash
# Make sure PKL files are in Backend folder:
ls Backend/*.pkl

# Should see:
# best_model_without_family.pkl
# best_model_with_family.pkl
# shap_explainer_without_family.pkl
# shap_explainer_with_family.pkl
```

### "API key error"
```bash
# Check .env file exists in Backend folder:
cat Backend/.env

# Should contain:
# API_KEY=your_gemini_api_key
```

### "Tool not executing"
Check server console for errors. If you see tool call but no result, check mcp1.py loading.

## Summary

**The magic happens in 3 files:**
1. `test.py` - Routes everything
2. `mcp1.py` - Does the ML
3. Gemini - Understands & formats

**You just need to:**
1. Start server: `python test.py`
2. Send messages: Any HTTP client
3. Get results: Natural language + raw data

Done! 🎉

