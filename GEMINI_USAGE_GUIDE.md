# Gemini API Usage Guide

## ✅ Working Solution

Your Gemini API was hitting rate limits because:
1. **Quota exhausted** for `gemini-2.0-flash-exp` (free tier limit: 0)
2. **Wrong fallback model** - `gemini-1.5-flash-001` doesn't exist

## 🎯 Working Model

**Use: `models/gemini-2.5-flash`** ✅

This model has available quota and works perfectly!

## 📁 Files Created

### 1. `working_gemini_client.py` - Main Client
Simple, working Gemini client with:
- Automatic rate limiting (5s between requests)
- Uses the working model (`gemini-2.5-flash`)
- Integrates with your MCP1 toxicity prediction functions
- Provides explanations for predictions

**Usage:**
```bash
# Ask a question
python working_gemini_client.py ask "What is cytotoxicity?"

# Predict toxicity for 10nm particle
python working_gemini_client.py predict 10

# Interactive chat
python working_gemini_client.py chat
```

### 2. `simple_toxicity_chat.py` - Easy Interface
User-friendly interface with menu options:
```bash
python simple_toxicity_chat.py
```

### 3. `find_working_model.py` - Model Discovery
Tests different models to find which ones have quota:
```bash
python find_working_model.py
```

### 4. `test_simple_gemini.py` - Testing Tool
Test basic API functionality:
```bash
# Single request test
python test_simple_gemini.py single

# List available models
python test_simple_gemini.py models

# Test rapid requests
python test_simple_gemini.py rapid 5 4
```

## 🔧 Fixed Issues

### MCP1.py Fix
Fixed the `_prepare_features` function to handle missing categorical columns:
```python
# Only encode categorical columns that exist in the dataframe
existing_categorical_cols = [col for col in categorical_cols if col in df.columns]
if existing_categorical_cols:
    df = pd.get_dummies(df, columns=existing_categorical_cols, dummy_na=False)
```

## 📊 Rate Limiting Strategy

The working client uses:
- **5 seconds** minimum delay between requests
- Tracks last request time
- Automatic waiting if needed

This respects the free tier limits:
- 15 requests per minute (RPM)
- Daily quota limits

## 🚀 Quick Start

### Option 1: Simple Question
```bash
python working_gemini_client.py ask "What could be the cytotoxicity for particle size 10 nm?"
```

### Option 2: Prediction with Explanation
```bash
python working_gemini_client.py predict 10
```

### Option 3: Interactive Chat
```bash
python working_gemini_client.py chat
```

Then type:
- `predict 10` - Run prediction for 10nm particle
- Any question about toxicity
- `quit` - Exit

## 📝 Example Output

```
🔬 Predicting toxicity for 10.0nm particle...
📋 Parameters: {'ParticleSize': 10.0, 'ZetaPotential': -20.0, 'Dose': 50.0, 
                'Time': 24.0, 'Solvent': 'Water', 'CellType': 'HeLa', 
                'CellOrigin': 'Human'}
✅ Prediction: NON-TOXIC
   Confidence: 0.793
   Toxic Probability: 0.207

🤖 Getting Gemini's explanation...
🤖 Gemini: The ML model's prediction of NON-TOXIC with 79.3% confidence means...
```

## ⚠️ Important Notes

1. **Wait between requests**: The client automatically waits 5s between requests
2. **Quota limits**: Free tier has daily limits - check at https://ai.dev/usage
3. **Model availability**: If `gemini-2.5-flash` gets rate limited, run `find_working_model.py` to find alternatives

## 🔍 Troubleshooting

### "Rate limit exceeded"
- Wait 1-2 minutes
- Check quota at: https://ai.dev/usage
- Try finding another model: `python find_working_model.py`

### "Model not found"
- Run: `python test_simple_gemini.py models`
- Update the model name in `working_gemini_client.py`

### "Prediction failed"
- Check that all 4 PKL files are present
- Verify parameters are correct types (float for numbers, string for text)

## 💡 Tips

1. **Use the working client** instead of test.py - it has proper rate limiting
2. **Wait 5+ seconds** between requests to avoid rate limits
3. **Check your quota** regularly at https://ai.dev/usage
4. **Use specific questions** for better responses from Gemini

## 🎓 Integration with Your App

To integrate into your FastAPI app (test.py):

1. Replace the model name:
   ```python
   PRIMARY_MODEL = "models/gemini-2.5-flash"  # Use this!
   ```

2. Increase the delay:
   ```python
   MIN_REQUEST_INTERVAL = 5.0  # 5 seconds minimum
   ```

3. Remove the fallback to non-existent models:
   ```python
   FALLBACK_MODEL = "models/gemini-2.0-flash"  # Not gemini-1.5-flash-001
   ```

4. Add longer wait times on rate limit:
   ```python
   wait_time = max(wait_time, 60) + 10  # Wait at least 60s + 10s buffer
   ```
