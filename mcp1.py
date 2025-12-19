"""
MCP1 - Machine Learning Prediction Functions
Implements toxicity prediction and explanation using pickled models
"""
import joblib
import pandas as pd
import numpy as np
import os

# Get the directory where this script is located
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Load all 4 PKL files at module import (only once)
print("Loading models from PKL files...")
try:
    MODEL_BASIC = joblib.load(os.path.join(BACKEND_DIR, "best_model_without_family.pkl"))
    MODEL_FAMILY = joblib.load(os.path.join(BACKEND_DIR, "best_model_with_family.pkl"))
    SHAP_BASIC = joblib.load(os.path.join(BACKEND_DIR, "shap_explainer_without_family.pkl"))
    SHAP_FAMILY = joblib.load(os.path.join(BACKEND_DIR, "shap_explainer_with_family.pkl"))
    print("✓ All 4 PKL files loaded successfully!")
except Exception as e:
    print(f"✗ Error loading PKL files: {e}")
    raise


def _prepare_features(input_dict, model_artifact):
    """
    Internal helper to transform raw input to model features
    
    Args:
        input_dict: Dictionary with raw input parameters
        model_artifact: Loaded model artifact with metadata
    
    Returns:
        pandas DataFrame with aligned features
    """
    feature_columns = model_artifact["feature_columns"]
    categorical_cols = model_artifact["categorical_cols"]
    num_cols = model_artifact["num_cols"]
    numeric_medians = model_artifact["numeric_medians"]
    
    # Create DataFrame from input
    df = pd.DataFrame([input_dict])
    
    # Fill numeric columns with medians if missing
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(numeric_medians.get(col, 0))
        else:
            # If column missing entirely, use median
            if col in feature_columns:
                df[col] = numeric_medians.get(col, 0)
    
    # One-hot encode categorical columns (only if they exist in the dataframe)
    existing_categorical_cols = [col for col in categorical_cols if col in df.columns]
    if existing_categorical_cols:
        df = pd.get_dummies(df, columns=existing_categorical_cols, dummy_na=False)
    
    # Align features to match training (add missing columns as 0)
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    # Return only the columns in the correct order
    return df[feature_columns]


def predict_toxicity_without_family(ParticleSize, ZetaPotential, Dose, Time,
                                     Solvent, CellType, CellOrigin):
    """
    Predict carbon dot toxicity WITHOUT plant family information
    
    Parameters:
    -----------
    ParticleSize : float
        Carbon dot particle size in nanometers (e.g., 7.5)
    ZetaPotential : float
        Surface charge in millivolts (e.g., -22.0)
    Dose : float
        Dosage concentration in µg/mL (e.g., 15.0)
    Time : float
        Exposure time in hours (e.g., 24)
    Solvent : str
        Extraction solvent (e.g., 'Ethanol', 'Water', 'Methanol')
    CellType : str
        Cell type tested (e.g., 'HeLa', 'MCF7', 'A549')
    CellOrigin : str
        Organism origin (e.g., 'Human', 'Mouse', 'Rat')
    
    Returns:
    --------
    dict with:
        - success: bool
        - prediction: int (0=non-toxic, 1=toxic)
        - class_label: str ('TOXIC' or 'NON-TOXIC')
        - probability_toxic: float [0-1]
        - probability_non_toxic: float [0-1]
        - confidence: float (max probability)
        - model_used: str
    """
    try:
        # Prepare input dictionary
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        # Transform features
        X = _prepare_features(input_dict, MODEL_BASIC)
        
        # Get model from artifact
        model = MODEL_BASIC["model"]
        
        # Make prediction
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0]
        
        # Return results
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(probabilities[1]),
            "probability_non_toxic": float(probabilities[0]),
            "confidence": float(max(probabilities)),
            "model_used": "without_family"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": None
        }


def predict_toxicity_with_family(ParticleSize, ZetaPotential, Dose, Time,
                                  Family, Solvent, CellType, CellOrigin):
    """
    Predict carbon dot toxicity WITH plant family information
    
    Parameters:
    -----------
    ParticleSize : float
        Carbon dot particle size in nanometers
    ZetaPotential : float
        Surface charge in millivolts
    Dose : float
        Dosage concentration in µg/mL
    Time : float
        Exposure time in hours
    Family : str
        Plant family name (e.g., 'Fabaceae', 'Rosaceae', 'Moraceae')
    Solvent : str
        Extraction solvent
    CellType : str
        Cell type tested
    CellOrigin : str
        Organism origin
    
    Returns:
    --------
    dict with prediction results (same format as without_family)
    """
    try:
        # Prepare input dictionary
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Family": str(Family),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        # Transform features
        X = _prepare_features(input_dict, MODEL_FAMILY)
        
        # Get model from artifact
        model = MODEL_FAMILY["model"]
        
        # Make prediction
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0]
        
        # Return results
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(probabilities[1]),
            "probability_non_toxic": float(probabilities[0]),
            "confidence": float(max(probabilities)),
            "model_used": "with_family"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": None
        }


def explain_toxicity_prediction_without_family(ParticleSize, ZetaPotential, Dose, Time,
                                                Solvent, CellType, CellOrigin,
                                                top_n=10, save_plot=False):
    """
    Explain toxicity prediction using SHAP (Explainable AI) WITHOUT plant family
    
    Parameters:
    -----------
    [Same as predict_toxicity_without_family]
    top_n : int, optional
        Number of top contributing features to return (default: 10)
    save_plot : bool, optional
        Whether to save waterfall plot (default: False)
    
    Returns:
    --------
    dict with:
        - success: bool
        - prediction: int
        - class_label: str
        - probability_toxic: float
        - confidence: float
        - base_value: float (SHAP expected value)
        - top_features: list of dicts with feature contributions
        - explanation: str (human-readable summary)
        - model_used: str
    """
    try:
        # Prepare input dictionary
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        # Transform features
        X = _prepare_features(input_dict, MODEL_BASIC)
        
        # Get model and explainer
        model = MODEL_BASIC["model"]
        explainer = SHAP_BASIC["explainer"]
        feature_columns = MODEL_BASIC["feature_columns"]
        
        # Make prediction
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0]
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X)
        
        # Handle binary classification (list of arrays)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Use positive class (toxic)
        
        # Flatten if needed
        if len(shap_values.shape) > 1:
            shap_values = shap_values.flatten()
        
        # Get base value (expected model output)
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[1] if len(base_value) > 1 else base_value[0])
        else:
            base_value = float(base_value)
        
        # Build feature contributions list
        n_features = min(len(shap_values), len(feature_columns))
        feature_contributions = []
        
        for i in range(n_features):
            feature_contributions.append({
                "feature": feature_columns[i],
                "value": float(X.iloc[0, i]),
                "shap_value": float(shap_values[i]),
                "abs_shap": float(abs(shap_values[i])),
                "impact": "increases risk" if shap_values[i] > 0 else "decreases risk"
            })
        
        # Sort by absolute SHAP value (most important first)
        feature_contributions.sort(key=lambda x: x["abs_shap"], reverse=True)
        
        # Get top N features
        top_features = feature_contributions[:int(top_n)]
        
        # Create human-readable explanation
        top_feat = top_features[0]
        explanation = (
            f"The model predicts {('TOXIC' if prediction == 1 else 'NON-TOXIC')} "
            f"with {max(probabilities)*100:.1f}% confidence. "
            f"The most important factor is {top_feat['feature']} "
            f"(SHAP value: {top_feat['shap_value']:.3f}), which "
            f"{top_feat['impact']}."
        )
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(probabilities[1]),
            "confidence": float(max(probabilities)),
            "base_value": base_value,
            "top_features": top_features,
            "all_features": feature_contributions,
            "explanation": explanation,
            "model_used": "without_family"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": None
        }


def explain_toxicity_prediction_with_family(ParticleSize, ZetaPotential, Dose, Time,
                                             Family, Solvent, CellType, CellOrigin,
                                             top_n=10, save_plot=False):
    """
    Explain toxicity prediction using SHAP (Explainable AI) WITH plant family
    
    Parameters:
    -----------
    [Same as predict_toxicity_with_family]
    top_n : int, optional
        Number of top contributing features to return (default: 10)
    save_plot : bool, optional
        Whether to save waterfall plot (default: False)
    
    Returns:
    --------
    dict with prediction, SHAP values, and explanations (same format as without_family)
    """
    try:
        # Prepare input dictionary
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Family": str(Family),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        # Transform features
        X = _prepare_features(input_dict, MODEL_FAMILY)
        
        # Get model and explainer
        model = MODEL_FAMILY["model"]
        explainer = SHAP_FAMILY["explainer"]
        feature_columns = MODEL_FAMILY["feature_columns"]
        
        # Make prediction
        prediction = int(model.predict(X)[0])
        probabilities = model.predict_proba(X)[0]
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(X)
        
        # Handle binary classification
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Flatten if needed
        if len(shap_values.shape) > 1:
            shap_values = shap_values.flatten()
        
        # Get base value
        base_value = explainer.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[1] if len(base_value) > 1 else base_value[0])
        else:
            base_value = float(base_value)
        
        # Build feature contributions list
        n_features = min(len(shap_values), len(feature_columns))
        feature_contributions = []
        
        for i in range(n_features):
            feature_contributions.append({
                "feature": feature_columns[i],
                "value": float(X.iloc[0, i]),
                "shap_value": float(shap_values[i]),
                "abs_shap": float(abs(shap_values[i])),
                "impact": "increases risk" if shap_values[i] > 0 else "decreases risk"
            })
        
        # Sort by absolute SHAP value
        feature_contributions.sort(key=lambda x: x["abs_shap"], reverse=True)
        
        # Get top N features
        top_features = feature_contributions[:int(top_n)]
        
        # Create explanation
        top_feat = top_features[0]
        explanation = (
            f"The model predicts {('TOXIC' if prediction == 1 else 'NON-TOXIC')} "
            f"with {max(probabilities)*100:.1f}% confidence. "
            f"The most important factor is {top_feat['feature']} "
            f"(SHAP value: {top_feat['shap_value']:.3f}), which "
            f"{top_feat['impact']}."
        )
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(probabilities[1]),
            "confidence": float(max(probabilities)),
            "base_value": base_value,
            "top_features": top_features,
            "all_features": feature_contributions,
            "explanation": explanation,
            "model_used": "with_family"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": None
        }


# Function dispatcher for easy tool execution
AVAILABLE_FUNCTIONS = {
    "predict_toxicity_without_family": predict_toxicity_without_family,
    "predict_toxicity_with_family": predict_toxicity_with_family,
    "explain_toxicity_prediction_without_family": explain_toxicity_prediction_without_family,
    "explain_toxicity_prediction_with_family": explain_toxicity_prediction_with_family
}


def execute_function(function_name, **kwargs):
    """
    Execute a function by name with given arguments
    
    Parameters:
    -----------
    function_name : str
        Name of the function to execute
    **kwargs : dict
        Function arguments
    
    Returns:
    --------
    dict with function result or error
    """
    if function_name not in AVAILABLE_FUNCTIONS:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}. Available: {list(AVAILABLE_FUNCTIONS.keys())}"
        }
    
    try:
        func = AVAILABLE_FUNCTIONS[function_name]
        result = func(**kwargs)
        return result
    except TypeError as e:
        return {
            "success": False,
            "error": f"Invalid arguments for {function_name}: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing {function_name}: {str(e)}"
        }


# Example usage / testing
if __name__ == "__main__":
    print("\n" + "="*70)
    print("MCP1 - Testing All Functions")
    print("="*70)
    
    # Test 1: Predict without family
    print("\n[Test 1] Predict without family")
    result1 = predict_toxicity_without_family(
        ParticleSize=7.5,
        ZetaPotential=-22.0,
        Dose=15.0,
        Time=24,
        Solvent="Ethanol",
        CellType="HeLa",
        CellOrigin="Human"
    )
    print(f"Result: {result1['class_label']} (confidence: {result1['confidence']:.3f})")
    
    # Test 2: Predict with family
    print("\n[Test 2] Predict with family")
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
    print(f"Result: {result2['class_label']} (confidence: {result2['confidence']:.3f})")
    
    # Test 3: Explain without family
    print("\n[Test 3] Explain without family")
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
    print(f"Explanation: {result3['explanation']}")
    print(f"Top 3 features:")
    for feat in result3['top_features'][:3]:
        print(f"  - {feat['feature']}: SHAP={feat['shap_value']:.3f} ({feat['impact']})")
    
    # Test 4: Explain with family
    print("\n[Test 4] Explain with family")
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
    print(f"Explanation: {result4['explanation']}")
    print(f"Top 3 features:")
    for feat in result4['top_features'][:3]:
        print(f"  - {feat['feature']}: SHAP={feat['shap_value']:.3f} ({feat['impact']})")
    
    # Test 5: Execute via dispatcher
    print("\n[Test 5] Execute via dispatcher")
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
    print(f"Result: {result5['class_label']} (prob toxic: {result5['probability_toxic']:.3f})")
    
    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70)
