# Carbon Dot Toxicity Prediction API

FastAPI backend with Google Gemini AI integration for predicting carbon dot nanoparticle toxicity using machine learning and explainable AI (SHAP).

## Features

- 🤖 **Gemini AI Integration**: Natural language interface with function calling
- 🧠 **ML Models**: Random Forest classifiers for toxicity prediction
- 📊 **Explainable AI**: SHAP values explain model decisions
- 🔧 **4 Tool Functions**: Predictions and explanations with/without plant family
- ⚡ **FastAPI**: High-performance async API
- 🎯 **CORS Enabled**: Ready for frontend integration

## Quick Start

### 1. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file:

```env
API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

### 3. Verify Models

Make sure these PKL files are in the Backend folder:
- `best_model_without_family.pkl`
- `best_model_with_family.pkl`
- `shap_explainer_without_family.pkl`
- `shap_explainer_with_family.pkl`

### 4. Start Server

```bash
python test.py
```

Server starts at: `http://localhost:8000`

### 5. Test the API

In another terminal:

```bash
python test_client.py
```

## API Endpoints

### POST `/message`

Send a chat message and get AI-powered toxicity predictions.

**Request:**
```json
{
    "text": "Is a 7.5nm carbon dot toxic at 15 µg/mL for 24 hours?"
}
```

**Response:**
```json
{
    "success": true,
    "text": "Based on the prediction, the carbon dot is NON-TOXIC with 85.9% confidence...",
    "tool_calls": [
        {
            "function": "predict_toxicity_without_family",
            "arguments": {...},
            "result": {
                "prediction": 0,
                "class_label": "NON-TOXIC",
                "probability_toxic": 0.141,
                "confidence": 0.859
            }
        }
    ]
}
```

### GET `/health`

Check API health and available tools.

**Response:**
```json
{
    "status": "healthy",
    "models_loaded": true,
    "tools_available": [
        "predict_toxicity_without_family",
        "predict_toxicity_with_family",
        "explain_toxicity_prediction_without_family",
        "explain_toxicity_prediction_with_family"
    ]
}
```

## Available Tools

### 1. `predict_toxicity_without_family`

Predict toxicity without plant family information.

**Required Parameters:**
- `ParticleSize` (number): Particle size in nm
- `ZetaPotential` (number): Surface charge in mV
- `Dose` (number): Concentration in µg/mL
- `Time` (number): Exposure time in hours
- `Solvent` (string): Extraction solvent
- `CellType` (string): Cell line
- `CellOrigin` (string): Species (Human/Mouse/Rat)

### 2. `predict_toxicity_with_family`

Predict toxicity with plant family information.

**Additional Parameter:**
- `Family` (string): Plant family name

### 3. `explain_toxicity_prediction_without_family`

Get SHAP explanation for prediction (no family).

**Optional Parameters:**
- `top_n` (integer): Number of top features (default: 10)
- `save_plot` (boolean): Save waterfall plot (default: false)

### 4. `explain_toxicity_prediction_with_family`

Get SHAP explanation with plant family.

## Example Conversations

### Simple Prediction

**User:** "Is a 10nm carbon dot toxic at 50 µg/mL for 24h? ZetaPotential: -20mV, Solvent: Water, CellType: HeLa, CellOrigin: Human"

**AI:** Calls `predict_toxicity_without_family` → Returns prediction with confidence

### Request Explanation

**User:** "Why is it toxic?"

**AI:** Calls `explain_toxicity_prediction_without_family` → Returns top SHAP features explaining the prediction

### Missing Parameters

**User:** "Is a 5nm particle toxic?"

**AI:** Asks for missing parameters (Dose, Time, Solvent, etc.)

## Architecture

```
Backend/
├── test.py                          # FastAPI server + Gemini integration
├── ml_functions.py                  # ML prediction & SHAP explanation functions
├── test_client.py                   # Test client
├── requirements.txt                 # Dependencies
├── .env                             # API keys (create this)
└── *.pkl                            # Model files (4 files)
```

## How It Works

1. **User sends message** via `/message` endpoint
2. **Gemini AI** analyzes the message and decides if tools are needed
3. **Tool calls** are executed by `ml_functions.py`:
   - Load pickled models with joblib
   - Transform input features
   - Make predictions
   - Calculate SHAP values
4. **Results** are sent back to Gemini
5. **Gemini formats response** in natural language
6. **Response returned** to user

## Development

### Adding New Tools

1. Add function to `ml_functions.py`
2. Add to `FUNCTION_MAP` dictionary
3. Create `FunctionDeclaration` in `test.py`
4. Add to `toxicity_toolkit`

### Debugging

Enable verbose logging in `test.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Individual Functions

```python
from ml_functions import predict_toxicity_without_family

result = predict_toxicity_without_family(
    ParticleSize=7.5,
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human"
)

print(result)
```

## Frontend Integration

### React/Vue/Angular

```javascript
async function predictToxicity(message) {
    const response = await fetch('http://localhost:8000/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: message })
    });
    
    const data = await response.json();
    return data;
}

// Usage
const result = await predictToxicity(
    "Is a 10nm carbon dot toxic at 50 µg/mL?"
);

console.log(result.text);  // AI response
console.log(result.tool_calls);  // Tool execution details
```

## Troubleshooting

### Models not loading

```
FileNotFoundError: best_model_without_family.pkl
```

**Solution:** Copy all 4 PKL files to the Backend folder

### Gemini API Error

```
google.genai.errors.APIError: 401
```

**Solution:** Check your API key in `.env` file

### Import Error

```
ModuleNotFoundError: No module named 'google.genai'
```

**Solution:** Run `pip install -r requirements.txt`

### CORS Error in Frontend

```
Access-Control-Allow-Origin error
```

**Solution:** Add your frontend URL to `origins` list in `test.py`

## Performance

| Operation                    | Time       |
|------------------------------|------------|
| Model loading (startup)      | ~2-3s      |
| Simple prediction           | ~50-100ms  |
| Prediction with SHAP        | ~100-200ms |
| Full conversation (1 tool)  | ~1-2s      |

## Security Notes

- Never commit `.env` file with real API keys
- Use environment variables in production
- Add rate limiting for production deployment
- Validate all inputs before model inference

## License

MIT

