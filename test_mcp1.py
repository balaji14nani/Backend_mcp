"""
Test script for mcp1.py functions
Tests all 4 functions directly
"""
from mcp1 import (
    predict_toxicity_without_family,
    predict_toxicity_with_family,
    explain_toxicity_prediction_without_family,
    explain_toxicity_prediction_with_family,
    execute_function
)

print("\n" + "="*70)
print("Testing MCP1.py - All 4 Functions")
print("="*70)

# Test 1: Predict without family
print("\n" + "-"*70)
print("[1/4] Testing predict_toxicity_without_family")
print("-"*70)

result1 = predict_toxicity_without_family(
    ParticleSize=7.5,
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human"
)

if result1["success"]:
    print(f"✓ Success!")
    print(f"  Prediction: {result1['class_label']}")
    print(f"  Probability (Toxic): {result1['probability_toxic']:.3f}")
    print(f"  Confidence: {result1['confidence']:.3f}")
else:
    print(f"✗ Error: {result1.get('error')}")

# Test 2: Predict with family
print("\n" + "-"*70)
print("[2/4] Testing predict_toxicity_with_family")
print("-"*70)

result2 = predict_toxicity_with_family(
    ParticleSize=10.0,
    ZetaPotential=-18.0,
    Dose=50.0,
    Time=48,
    Family="Fabaceae",
    Solvent="Water",
    CellType="MCF7",
    CellOrigin="Human"
)

if result2["success"]:
    print(f"✓ Success!")
    print(f"  Prediction: {result2['class_label']}")
    print(f"  Probability (Toxic): {result2['probability_toxic']:.3f}")
    print(f"  Confidence: {result2['confidence']:.3f}")
else:
    print(f"✗ Error: {result2.get('error')}")

# Test 3: Explain without family
print("\n" + "-"*70)
print("[3/4] Testing explain_toxicity_prediction_without_family")
print("-"*70)

result3 = explain_toxicity_prediction_without_family(
    ParticleSize=7.5,
    ZetaPotential=-22.0,
    Dose=15.0,
    Time=24,
    Solvent="Ethanol",
    CellType="HeLa",
    CellOrigin="Human",
    top_n=5
)

if result3["success"]:
    print(f"✓ Success!")
    print(f"  Prediction: {result3['class_label']}")
    print(f"  Base Value: {result3['base_value']:.3f}")
    print(f"  Explanation: {result3['explanation']}")
    print(f"\n  Top 5 Features:")
    for i, feat in enumerate(result3['top_features'][:5], 1):
        print(f"    {i}. {feat['feature']:30s} SHAP={feat['shap_value']:7.3f} ({feat['impact']})")
else:
    print(f"✗ Error: {result3.get('error')}")

# Test 4: Explain with family
print("\n" + "-"*70)
print("[4/4] Testing explain_toxicity_prediction_with_family")
print("-"*70)

result4 = explain_toxicity_prediction_with_family(
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

if result4["success"]:
    print(f"✓ Success!")
    print(f"  Prediction: {result4['class_label']}")
    print(f"  Base Value: {result4['base_value']:.3f}")
    print(f"  Explanation: {result4['explanation']}")
    print(f"\n  Top 5 Features:")
    for i, feat in enumerate(result4['top_features'][:5], 1):
        print(f"    {i}. {feat['feature']:30s} SHAP={feat['shap_value']:7.3f} ({feat['impact']})")
else:
    print(f"✗ Error: {result4.get('error')}")

# Test 5: Execute via dispatcher
print("\n" + "-"*70)
print("[5/5] Testing execute_function dispatcher")
print("-"*70)

result5 = execute_function(
    "predict_toxicity_without_family",
    ParticleSize=5.0,
    ZetaPotential=-25.0,
    Dose=10.0,
    Time=24,
    Solvent="Ethanol",
    CellType="A549",
    CellOrigin="Human"
)

if result5["success"]:
    print(f"✓ Success!")
    print(f"  Prediction: {result5['class_label']}")
    print(f"  Probability (Toxic): {result5['probability_toxic']:.3f}")
else:
    print(f"✗ Error: {result5.get('error')}")

# Summary
print("\n" + "="*70)
print("Test Summary")
print("="*70)
successes = sum([
    result1.get("success", False),
    result2.get("success", False),
    result3.get("success", False),
    result4.get("success", False),
    result5.get("success", False)
])
print(f"Passed: {successes}/5 tests")
if successes == 5:
    print("✓ All tests passed! mcp1.py is working correctly.")
else:
    print("✗ Some tests failed. Check errors above.")
print("="*70 + "\n")

