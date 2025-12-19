# Gemini API Quota Management

## What Just Happened

You hit the **Gemini API free tier rate limit**:
- ❌ `gemini-2.0-flash-exp` - Experimental model with lower quotas
- ✅ **Fixed**: Switched to `gemini-1.5-flash` - Better free tier limits

## What I Fixed

### 1. Changed Model
```python
# Before (Low quota)
model="gemini-2.0-flash-exp"

# After (Better quota)
model="gemini-1.5-flash"
```

### 2. Added Retry Logic
```python
def call_gemini_with_retry(model, contents, config, max_retries=3):
    # Automatically retries with exponential backoff
    # Waits 30s+ when rate limited
    # Max 3 attempts
```

## Gemini API Free Tier Limits

| Model | Requests/Minute | Requests/Day | Tokens/Minute |
|-------|-----------------|--------------|---------------|
| gemini-1.5-flash | 15 | 1,500 | 1M input |
| gemini-1.5-pro | 2 | 50 | 32K input |
| gemini-2.0-flash-exp | **Lower** | **Lower** | **Lower** |

**Recommendation:** Use `gemini-1.5-flash` for development (best balance)

## Check Your Usage

1. **Google AI Studio Dashboard:**
   - Go to: https://ai.dev/usage?tab=rate-limit
   - View current usage
   - See remaining quota

2. **API Key Usage:**
   - Check: https://aistudio.google.com/app/apikey
   - Monitor quota consumption

## Solutions

### Solution 1: Wait (Already Implemented) ✅

The code now automatically:
- Detects rate limit errors
- Waits the suggested time
- Retries up to 3 times

**You don't need to do anything!**

### Solution 2: Reduce Request Frequency

**Limit requests in your frontend:**
```javascript
// Add debouncing
let timeout;
function sendMessage(text) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        fetch('/message', {...});
    }, 1000);  // Wait 1s between requests
}
```

### Solution 3: Upgrade API Plan

**For production use:**
1. Go to: https://ai.google.dev/pricing
2. Upgrade to **Pay-as-you-go**
3. Get higher limits:
   - 1,000+ requests/minute
   - 4M+ requests/day
   - More tokens

**Pricing (Pay-as-you-go):**
- gemini-1.5-flash: $0.075 per 1M input tokens
- gemini-1.5-pro: $1.25 per 1M input tokens

### Solution 4: Use Multiple API Keys

**For development:**
```python
# In test.py
API_KEYS = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2"),
    os.getenv("API_KEY_3"),
]

current_key_index = 0

def get_client():
    global current_key_index
    return genai.Client(api_key=API_KEYS[current_key_index])

def switch_api_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return get_client()
```

## Model Comparison

### gemini-1.5-flash ⭐ **RECOMMENDED**
- ✅ Fast responses
- ✅ Good free tier
- ✅ Supports function calling
- ✅ Best for development
- **Use this!**

### gemini-1.5-pro
- ✅ Better quality
- ❌ Lower free tier limits
- ✅ Supports function calling
- **Use for production**

### gemini-2.0-flash-exp
- ✅ Latest features
- ❌ Very low free tier
- ⚠️ Experimental (may change)
- **Avoid for now**

## Change Model Anytime

Edit `Backend/test.py`:

```python
# Line ~260 and ~330

# Option 1: Fast (Default) ✅
response = call_gemini_with_retry(
    model="gemini-1.5-flash",
    ...
)

# Option 2: Better Quality
response = call_gemini_with_retry(
    model="gemini-1.5-pro",
    ...
)

# Option 3: Experimental (Not recommended)
response = call_gemini_with_retry(
    model="gemini-2.0-flash-exp",
    ...
)
```

## Monitor Usage in Real-Time

### Add Usage Tracking

```python
# In test.py, add after each Gemini call:

if hasattr(response, 'usage_metadata'):
    usage = response.usage_metadata
    print(f"Token usage: {usage.prompt_token_count} in, {usage.candidates_token_count} out")
```

### Create Usage Endpoint

```python
# Add to test.py

@app.get("/usage")
def get_usage():
    """Check approximate usage"""
    # This is a placeholder - actual tracking requires storing request counts
    return {
        "model": "gemini-1.5-flash",
        "limits": {
            "requests_per_minute": 15,
            "requests_per_day": 1500
        },
        "tip": "Check actual usage at https://ai.dev/usage"
    }
```

## Rate Limit Best Practices

### 1. Cache Responses
```python
# Cache predictions for same inputs
cache = {}

def get_prediction(params):
    key = hash(str(params))
    if key in cache:
        return cache[key]
    
    result = execute_function(...)
    cache[key] = result
    return result
```

### 2. Batch Requests
```python
# Instead of:
for sample in samples:
    predict(sample)  # N API calls

# Do:
batch_predict(samples)  # 1 API call
```

### 3. Add Rate Limiting Middleware
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/message")
@limiter.limit("10/minute")  # Max 10 requests per minute per IP
def message(request: Request, msg: Message):
    ...
```

## Current Status

✅ **Fixed Issues:**
1. Switched to `gemini-1.5-flash` (better quotas)
2. Added automatic retry with backoff
3. Extracts wait time from error messages
4. Up to 3 retry attempts

✅ **What Happens Now:**
- If rate limited → Waits automatically
- Retries after wait period
- You see: `⚠️ Rate limit hit. Waiting 30s...`
- Then continues normally

## Testing

### Test Retry Logic
```bash
# Server will automatically handle rate limits
python test.py

# In another terminal
python test_client.py

# If rate limited, you'll see:
# ⚠️ Rate limit hit. Waiting 30s before retry 1/3...
```

### Test Different Models

**Edit test.py**, change line ~260:
```python
model="gemini-1.5-flash"  # Try this first
model="gemini-1.5-pro"    # Or this for better quality
```

Then restart server:
```bash
python test.py
```

## Error Messages Explained

### 429 RESOURCE_EXHAUSTED
```
"You exceeded your current quota"
```
**Meaning:** Too many requests  
**Solution:** Wait or upgrade plan  
**Auto-handled:** Yes ✅

### Invalid API Key
```
"API key not valid"
```
**Meaning:** Wrong/expired key  
**Solution:** Check `.env` file  
**Auto-handled:** No

### Model Not Found
```
"Model not found"
```
**Meaning:** Wrong model name  
**Solution:** Use `gemini-1.5-flash`  
**Auto-handled:** No

## Summary

### ✅ You're Good Now!

1. **Model changed** to `gemini-1.5-flash`
2. **Retry logic added** - auto-handles rate limits
3. **Better free tier** - 15 requests/min instead of lower

### 🚀 Just Run It

```bash
python test.py
```

It will automatically:
- Use the better model
- Retry when rate limited
- Wait the appropriate time
- Continue working

### 📊 Monitor Usage

Check: https://ai.dev/usage?tab=rate-limit

### 💰 Upgrade Later

When ready for production:
- Upgrade to Pay-as-you-go
- Get 1000+ requests/minute
- ~$0.075 per 1M tokens

Done! Your API should work now. 🎉

