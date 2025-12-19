"""
ML prediction and explanation functions for Gemini tool calling
"""
import joblib
import pandas as pd
import numpy as np
import os

# Get the directory where this script is located
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Load models once at startup
print("Loading models...")
model_basic_artifact = joblib.load(os.path.join(BACKEND_DIR, "best_model_without_family.pkl"))
model_family_artifact = joblib.load(os.path.join(BACKEND_DIR, "best_model_with_family.pkl"))
shap_basic_artifact = joblib.load(os.path.join(BACKEND_DIR, "shap_explainer_without_family.pkl"))
shap_family_artifact = joblib.load(os.path.join(BACKEND_DIR, "shap_explainer_with_family.pkl"))

# Extract components
model_basic = model_basic_artifact["model"]
feature_columns_basic = model_basic_artifact["feature_columns"]
categorical_cols_basic = model_basic_artifact["categorical_cols"]
num_cols_basic = model_basic_artifact["num_cols"]
numeric_medians_basic = model_basic_artifact["numeric_medians"]

model_family = model_family_artifact["model"]
feature_columns_family = model_family_artifact["feature_columns"]
categorical_cols_family = model_family_artifact["categorical_cols"]
num_cols_family = model_family_artifact["num_cols"]
numeric_medians_family = model_family_artifact["numeric_medians"]

explainer_basic = shap_basic_artifact['explainer']
explainer_family = shap_family_artifact['explainer']

print("✓ All models loaded successfully!")


def prepare_input(input_dict, feature_columns, categorical_cols, num_cols, numeric_medians):
    """Transform raw input to model-ready features"""
    df = pd.DataFrame([input_dict])
    
    # Fill numeric columns
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(numeric_medians.get(col, 0))
        else:
            if col in feature_columns:
                df[col] = numeric_medians.get(col, 0)
    
    # One-hot encode
    df = pd.get_dummies(df, columns=categorical_cols, dummy_na=False)
    
    # Align features
    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[feature_columns]


def predict_toxicity_without_family(ParticleSize, ZetaPotential, Dose, Time, 
                                     Solvent, CellType, CellOrigin):
    """
    Predict toxicity without plant family information
    
    Returns:
        dict with prediction, probability, and class label
    """
    try:
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        X = prepare_input(input_dict, feature_columns_basic, categorical_cols_basic, 
                         num_cols_basic, numeric_medians_basic)
        
        prediction = int(model_basic.predict(X)[0])
        proba = model_basic.predict_proba(X)[0]
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(proba[1]),
            "probability_non_toxic": float(proba[0]),
            "confidence": float(max(proba)),
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
    Predict toxicity with plant family information
    
    Returns:
        dict with prediction, probability, and class label
    """
    try:
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
        
        X = prepare_input(input_dict, feature_columns_family, categorical_cols_family,
                         num_cols_family, numeric_medians_family)
        
        prediction = int(model_family.predict(X)[0])
        proba = model_family.predict_proba(X)[0]
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(proba[1]),
            "probability_non_toxic": float(proba[0]),
            "confidence": float(max(proba)),
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
    Explain toxicity prediction with SHAP (without family)
    
    Returns:
        dict with prediction, SHAP values, and top contributing features
    """
    try:
        input_dict = {
            "ParticleSize": float(ParticleSize),
            "ZetaPotential": float(ZetaPotential),
            "Dose": float(Dose),
            "Time": float(Time),
            "Solvent": str(Solvent),
            "CellType": str(CellType),
            "CellOrigin": str(CellOrigin)
        }
        
        X = prepare_input(input_dict, feature_columns_basic, categorical_cols_basic,
                         num_cols_basic, numeric_medians_basic)
        
        # Get prediction
        prediction = int(model_basic.predict(X)[0])
        proba = model_basic.predict_proba(X)[0]
        
        # Get SHAP values
        shap_values = explainer_basic.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Positive class
        if len(shap_values.shape) > 1:
            shap_values = shap_values.flatten()
        
        # Get base value
        base_value = explainer_basic.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[1] if len(base_value) > 1 else base_value[0])
        else:
            base_value = float(base_value)
        
        # Build feature contributions
        n_features = min(len(shap_values), len(feature_columns_basic))
        feature_contributions = []
        for i in range(n_features):
            feature_contributions.append({
                'feature': feature_columns_basic[i],
                'value': float(X.iloc[0, i]),
                'shap_value': float(shap_values[i]),
                'abs_shap': float(abs(shap_values[i]))
            })
        
        feature_contributions.sort(key=lambda x: x['abs_shap'], reverse=True)
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(proba[1]),
            "confidence": float(max(proba)),
            "base_value": base_value,
            "top_features": feature_contributions[:int(top_n)],
            "explanation": f"The model predicts {('TOXIC' if prediction == 1 else 'NON-TOXIC')} with {max(proba)*100:.1f}% confidence. Top contributor: {feature_contributions[0]['feature']} (SHAP: {feature_contributions[0]['shap_value']:.3f})",
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
    Explain toxicity prediction with SHAP (with family)
    
    Returns:
        dict with prediction, SHAP values, and top contributing features
    """
    try:
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
        
        X = prepare_input(input_dict, feature_columns_family, categorical_cols_family,
                         num_cols_family, numeric_medians_family)
        
        # Get prediction
        prediction = int(model_family.predict(X)[0])
        proba = model_family.predict_proba(X)[0]
        
        # Get SHAP values
        shap_values = explainer_family.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        if len(shap_values.shape) > 1:
            shap_values = shap_values.flatten()
        
        # Get base value
        base_value = explainer_family.expected_value
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[1] if len(base_value) > 1 else base_value[0])
        else:
            base_value = float(base_value)
        
        # Build feature contributions
        n_features = min(len(shap_values), len(feature_columns_family))
        feature_contributions = []
        for i in range(n_features):
            feature_contributions.append({
                'feature': feature_columns_family[i],
                'value': float(X.iloc[0, i]),
                'shap_value': float(shap_values[i]),
                'abs_shap': float(abs(shap_values[i]))
            })
        
        feature_contributions.sort(key=lambda x: x['abs_shap'], reverse=True)
        
        return {
            "success": True,
            "prediction": prediction,
            "class_label": "TOXIC" if prediction == 1 else "NON-TOXIC",
            "probability_toxic": float(proba[1]),
            "confidence": float(max(proba)),
            "base_value": base_value,
            "top_features": feature_contributions[:int(top_n)],
            "explanation": f"The model predicts {('TOXIC' if prediction == 1 else 'NON-TOXIC')} with {max(proba)*100:.1f}% confidence. Top contributor: {feature_contributions[0]['feature']} (SHAP: {feature_contributions[0]['shap_value']:.3f})",
            "model_used": "with_family"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prediction": None
        }


# Function dispatcher
FUNCTION_MAP = {
    "predict_toxicity_without_family": predict_toxicity_without_family,
    "predict_toxicity_with_family": predict_toxicity_with_family,
    "explain_toxicity_prediction_without_family": explain_toxicity_prediction_without_family,
    "explain_toxicity_prediction_with_family": explain_toxicity_prediction_with_family
}


def execute_tool_call(function_name, arguments):
    """
    Execute a tool call and return the result
    
    Args:
        function_name: Name of the function to call
        arguments: Dictionary of arguments
    
    Returns:
        Result dictionary
    """
    if function_name not in FUNCTION_MAP:
        return {
            "success": False,
            "error": f"Unknown function: {function_name}"
        }
    
    try:
        func = FUNCTION_MAP[function_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing {function_name}: {str(e)}"
        }

