# MCP1.py - Function Implementation Guide

Complete implementation of ML prediction functions that load and use PKL files.

## Overview

`mcp1.py` implements all 4 toxicity prediction functions:
1. ✅ `predict_toxicity_without_family` - Basic prediction
2. ✅ `predict_toxicity_with_family` - Prediction with plant family
3. ✅ `explain_toxicity_prediction_without_family` - SHAP explanation
4. ✅ `explain_toxicity_prediction_with_family` - SHAP with family

## What Happens on Import

```python
from mcp1 import predict_toxicity_without_family

# At import time, all 4 PKL files are loaded ONCE:
# ✓ best_model_without_family.pkl
# ✓ best_model_with_family.pkl
# ✓ shap_explainer_without_family.pkl
# ✓ shap_explainer_with_family.pkl
```

Models stay in memory for fast predictions!

## Function 1: `predict_toxicity_without_family`

### Basic Usage

```python
from mcp1 import predict_toxicity_without_family

result = predict_toxicity_without_family(
    ParticleSize=7.5,        # nm
    ZetaPotential=-22.0,     # mV
    Dose=15.0,               # µg/mL
    Time=24,                 # hours
    Solvent="Ethanol",       # solvent name
    CellType="HeLa",         # cell line
    CellOrigin="Human"       # species
)

print(result)
```

### Output Format

```python
{
    "success": True,
    "prediction": 0,                      # 0=non-toxic, 1=toxic
    "class_label": "NON-TOXIC",
    "probability_toxic": 0.141,           # P(toxic)
    "probability_non_toxic": 0.859,       # P(non-toxic)
    "confidence": 0.859,                  # max(probabilities)
    "model_used": "without_family"
}
```

### Example with Error

```python
result = predict_toxicity_without_family(
    ParticleSize="invalid",  # Wrong type!
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human"
)

# Returns:
{
    "success": False,
    "error": "could not convert string to float: 'invalid'",
    "prediction": None
}
```

## Function 2: `predict_toxicity_with_family`

### Usage

```python
from mcp1 import predict_toxicity_with_family

result = predict_toxicity_with_family(
    ParticleSize=10.0,
    ZetaPotential=-18.0,
    Dose=50.0,
    Time=48,
    Family="Fabaceae",       # Additional parameter!
    Solvent="Water",
    CellType="MCF7",
    CellOrigin="Human"
)
```

### Output

Same format as `predict_toxicity_without_family`, but:
```python
{
    ...
    "model_used": "with_family"  # Different model used
}
```

## Function 3: `explain_toxicity_prediction_without_family`

### Usage

```python
from mcp1 import explain_toxicity_prediction_without_family

result = explain_toxicity_prediction_without_family(
    ParticleSize=7.5,
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human",
    top_n=10,           # Optional: number of features to return
    save_plot=False     # Optional: save waterfall plot
)
```

### Output

```python
{
    "success": True,
    "prediction": 0,
    "class_label": "NON-TOXIC",
    "probability_toxic": 0.141,
    "confidence": 0.859,
    "base_value": 0.500,        # SHAP expected value
    
    "top_features": [           # Top N most important features
        {
            "feature": "ZetaPotential",
            "value": -22.0,
            "shap_value": -0.120,       # Negative = reduces risk
            "abs_shap": 0.120,
            "impact": "decreases risk"
        },
        {
            "feature": "ParticleSize",
            "value": 7.5,
            "shap_value": 0.132,        # Positive = increases risk
            "abs_shap": 0.132,
            "impact": "increases risk"
        },
        # ... more features
    ],
    
    "all_features": [...],      # All features (not just top N)
    
    "explanation": "The model predicts NON-TOXIC with 85.9% confidence. The most important factor is ZetaPotential (SHAP value: -0.120), which decreases risk.",
    
    "model_used": "without_family"
}
```

### Understanding SHAP Values

```python
# SHAP Value Interpretation:
#   Positive (+) → Feature INCREASES toxicity risk
#   Negative (-) → Feature DECREASES toxicity risk
#   Larger absolute value → More important

# Example:
{
    "feature": "Dose",
    "shap_value": 0.085,         # Positive
    "impact": "increases risk"   # Higher dose = more toxic
}

{
    "feature": "ZetaPotential",
    "shap_value": -0.120,        # Negative
    "impact": "decreases risk"   # More negative charge = less toxic
}
```

## Function 4: `explain_toxicity_prediction_with_family`

### Usage

```python
from mcp1 import explain_toxicity_prediction_with_family

result = explain_toxicity_prediction_with_family(
    ParticleSize=10.0,
    ZetaPotential=-18.0,
    Dose=50.0,
    Time=48,
    Family="Fabaceae",
    Solvent="Water",
    CellType="MCF7",
    CellOrigin="Human",
    top_n=5
)
```

### Output

Same format as `explain_toxicity_prediction_without_family`, includes Family features in SHAP values.

## Execute via Dispatcher

### Usage

```python
from mcp1 import execute_function

# Call any function by name
result = execute_function(
    "predict_toxicity_without_family",  # Function name as string
    ParticleSize=7.5,                   # Pass arguments as kwargs
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human"
)
```

### Why Use Dispatcher?

Perfect for **dynamic function calling** (e.g., from Gemini AI tool calls):

```python
# Gemini returns:
tool_call = {
    "name": "predict_toxicity_without_family",
    "args": {"ParticleSize": 7.5, ...}
}

# Execute dynamically:
result = execute_function(tool_call["name"], **tool_call["args"])
```

## Integration with test.py (FastAPI + Gemini)

```python
# In test.py:
from mcp1 import execute_function

# When Gemini calls a tool:
func_name = "predict_toxicity_without_family"
func_args = {"ParticleSize": 7.5, ...}

# Execute via mcp1.py:
result = execute_function(func_name, **func_args)

# Return result to Gemini:
return result
```

## Testing

### Test All Functions

```bash
python test_mcp1.py
```

### Test Individual Function

```bash
python mcp1.py
```

### Import in Your Code

```python
# Option 1: Import specific functions
from mcp1 import predict_toxicity_without_family, explain_toxicity_prediction_without_family

# Option 2: Import all
from mcp1 import *

# Option 3: Import dispatcher
from mcp1 import execute_function
```

## Common Use Cases

### Case 1: Simple Prediction

```python
from mcp1 import predict_toxicity_without_family

result = predict_toxicity_without_family(
    ParticleSize=5.0,
    ZetaPotential=-25.0,
    Dose=10.0,
    Time=24,
    Solvent="Water",
    CellType="HeLa",
    CellOrigin="Human"
)

if result["success"]:
    print(f"Prediction: {result['class_label']}")
    print(f"Confidence: {result['confidence']:.1%}")
```

### Case 2: Get Top 3 Most Important Features

```python
from mcp1 import explain_toxicity_prediction_without_family

result = explain_toxicity_prediction_without_family(
    ParticleSize=10.0,
    ZetaPotential=-15.0,
    Dose=50.0,
    Time=48,
    Solvent="Water",
    CellType="MCF7",
    CellOrigin="Human",
    top_n=3
)

if result["success"]:
    print(f"Prediction: {result['class_label']}")
    print("\nTop 3 Contributing Factors:")
    for i, feat in enumerate(result['top_features'], 1):
        print(f"{i}. {feat['feature']}: {feat['impact']}")
```

### Case 3: Batch Predictions

```python
from mcp1 import predict_toxicity_without_family

samples = [
    {"ParticleSize": 5.0, "ZetaPotential": -25.0, "Dose": 10.0, ...},
    {"ParticleSize": 10.0, "ZetaPotential": -20.0, "Dose": 25.0, ...},
    {"ParticleSize": 15.0, "ZetaPotential": -15.0, "Dose": 50.0, ...}
]

results = []
for sample in samples:
    result = predict_toxicity_without_family(**sample)
    results.append(result)

# Analyze results
toxic_count = sum(1 for r in results if r["prediction"] == 1)
print(f"Toxic samples: {toxic_count}/{len(samples)}")
```

### Case 4: Compare With and Without Family

```python
from mcp1 import predict_toxicity_without_family, predict_toxicity_with_family

params_basic = {
    "ParticleSize": 8.0,
    "ZetaPotential": -20.0,
    "Dose": 30.0,
    "Time": 36,
    "Solvent": "Ethanol",
    "CellType": "HeLa",
    "CellOrigin": "Human"
}

params_with_family = {**params_basic, "Family": "Fabaceae"}

result1 = predict_toxicity_without_family(**params_basic)
result2 = predict_toxicity_with_family(**params_with_family)

print(f"Without Family: {result1['probability_toxic']:.3f}")
print(f"With Family:    {result2['probability_toxic']:.3f}")
print(f"Difference:     {abs(result1['probability_toxic'] - result2['probability_toxic']):.3f}")
```

## Error Handling

### Check for Success

```python
result = predict_toxicity_without_family(...)

if result["success"]:
    # Use prediction
    print(f"Prediction: {result['class_label']}")
else:
    # Handle error
    print(f"Error: {result['error']}")
```

### Common Errors

```python
# Missing required parameter
result = predict_toxicity_without_family(
    ParticleSize=7.5
    # Missing other parameters!
)
# → TypeError: missing required arguments

# Wrong type
result = predict_toxicity_without_family(
    ParticleSize="seven",  # Should be number
    ...
)
# → success=False, error="could not convert string to float"

# Unknown function
result = execute_function("unknown_function", ...)
# → success=False, error="Unknown function: unknown_function"
```

## Performance

| Operation                          | Time     |
|------------------------------------|----------|
| First import (load PKL files)      | ~2-3s    |
| Simple prediction                  | ~10-20ms |
| Explanation with SHAP              | ~50-100ms|
| Batch (100 predictions)            | ~1-2s    |

## Files Required

```
Backend/
├── mcp1.py                           # ← This file
├── best_model_without_family.pkl     # ← Required
├── best_model_with_family.pkl        # ← Required
├── shap_explainer_without_family.pkl # ← Required
└── shap_explainer_with_family.pkl    # ← Required
```

All 4 PKL files MUST be in the same folder as `mcp1.py`!

## Summary

```python
# Import
from mcp1 import (
    predict_toxicity_without_family,
    predict_toxicity_with_family,
    explain_toxicity_prediction_without_family,
    explain_toxicity_prediction_with_family,
    execute_function
)

# Use
result = predict_toxicity_without_family(
    ParticleSize=7.5,
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human"
)

# Check
if result["success"]:
    print(result["class_label"])
else:
    print(result["error"])
```

Done! 🚀

