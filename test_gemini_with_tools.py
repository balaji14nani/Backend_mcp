#!/usr/bin/env python3
"""
Test Gemini with MCP1 Tools
Combines the simple Gemini client with your toxicity prediction tools
"""
import os
import json
from simple_gemini_client import GeminiClient
from mcp1 import execute_function

def test_toxicity_prediction():
    """Test the toxicity prediction workflow"""
    
    # Initialize Gemini client
    print("🚀 Initializing Gemini client...")
    client = GeminiClient()
    
    # Test questions about toxicity
    test_questions = [
        "What could be the cytotoxicity for particle size 10 nm?",
        "Explain carbon dot toxicity factors",
        "What parameters do I need to predict nanoparticle toxicity?"
    ]
    
    print("\n" + "="*70)
    print("🧪 Testing Gemini Responses")
    print("="*70)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[Test {i}] Question: {question}")
        print("-" * 50)
        
        result = client.generate_content(question, temperature=0.3)
        
        if result["success"]:
            print(f"✅ Gemini Response:\n{result['content']}")
        else:
            print(f"❌ Failed: {result['error']}")
        
        print("\n" + "="*50)

def test_mcp_functions():
    """Test the MCP1 functions directly"""
    
    print("\n" + "="*70)
    print("🔬 Testing MCP1 Functions Directly")
    print("="*70)
    
    # Test 1: Predict without family
    print("\n[Test 1] Predict toxicity without family")
    result1 = execute_function(
        "predict_toxicity_without_family",
        ParticleSize=10.0,
        ZetaPotential=-20.0,
        Dose=50.0,
        Time=24,
        Solvent="Water",
        CellType="HeLa",
        CellOrigin="Human"
    )
    
    if result1["success"]:
        print(f"✅ Prediction: {result1['class_label']}")
        print(f"   Confidence: {result1['confidence']:.3f}")
        print(f"   Toxic probability: {result1['probability_toxic']:.3f}")
    else:
        print(f"❌ Error: {result1['error']}")
    
    # Test 2: Predict with family
    print("\n[Test 2] Predict toxicity with family")
    result2 = execute_function(
        "predict_toxicity_with_family",
        ParticleSize=10.0,
        ZetaPotential=-20.0,
        Dose=50.0,
        Time=24,
        Family="Fabaceae",
        Solvent="Water",
        CellType="HeLa",
        CellOrigin="Human"
    )
    
    if result2["success"]:
        print(f"✅ Prediction: {result2['class_label']}")
        print(f"   Confidence: {result2['confidence']:.3f}")
        print(f"   Toxic probability: {result2['probability_toxic']:.3f}")
    else:
        print(f"❌ Error: {result2['error']}")
    
    # Test 3: Explain prediction
    print("\n[Test 3] Explain prediction (without family)")
    result3 = execute_function(
        "explain_toxicity_prediction_without_family",
        ParticleSize=10.0,
        ZetaPotential=-20.0,
        Dose=50.0,
        Time=24,
        Solvent="Water",
        CellType="HeLa",
        CellOrigin="Human",
        top_n=5
    )
    
    if result3["success"]:
        print(f"✅ Explanation: {result3['explanation']}")
        print("   Top contributing factors:")
        for feat in result3['top_features'][:3]:
            print(f"     - {feat['feature']}: {feat['shap_value']:.3f} ({feat['impact']})")
    else:
        print(f"❌ Error: {result3['error']}")

def interactive_toxicity_chat():
    """Interactive chat for toxicity questions"""
    
    client = GeminiClient()
    
    print("\n" + "="*70)
    print("💬 Interactive Toxicity Chat")
    print("="*70)
    print("Ask questions about carbon dot toxicity!")
    print("Type 'predict' to run a prediction example")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'predict':
                print("\n🔬 Running prediction example...")
                
                # Run a prediction
                result = execute_function(
                    "predict_toxicity_without_family",
                    ParticleSize=10.0,
                    ZetaPotential=-20.0,
                    Dose=50.0,
                    Time=24,
                    Solvent="Water",
                    CellType="HeLa",
                    CellOrigin="Human"
                )
                
                if result["success"]:
                    print(f"✅ Prediction Result:")
                    print(f"   Class: {result['class_label']}")
                    print(f"   Confidence: {result['confidence']:.3f}")
                    print(f"   Toxic Probability: {result['probability_toxic']:.3f}")
                    
                    # Ask Gemini to explain this result
                    explanation_prompt = f"""
                    I ran a toxicity prediction for carbon dots with these parameters:
                    - Particle Size: 10.0 nm
                    - Zeta Potential: -20.0 mV  
                    - Dose: 50.0 µg/mL
                    - Time: 24 hours
                    - Solvent: Water
                    - Cell Type: HeLa
                    - Cell Origin: Human
                    
                    The model predicted: {result['class_label']} with {result['confidence']:.1%} confidence.
                    
                    Can you explain what this means and what factors might contribute to this result?
                    """
                    
                    print("\n🤖 Getting Gemini's explanation...")
                    gemini_result = client.generate_content(explanation_prompt, temperature=0.3)
                    
                    if gemini_result["success"]:
                        print(f"\n🤖 Gemini Explanation:\n{gemini_result['content']}")
                    else:
                        print(f"❌ Gemini explanation failed: {gemini_result['error']}")
                else:
                    print(f"❌ Prediction failed: {result['error']}")
            
            else:
                # Send to Gemini
                result = client.generate_content(user_input, temperature=0.3)
                
                if result["success"]:
                    print(f"\n🤖 Gemini: {result['content']}")
                else:
                    print(f"❌ Error: {result['error']}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "gemini":
            test_toxicity_prediction()
        elif sys.argv[1] == "mcp":
            test_mcp_functions()
        elif sys.argv[1] == "chat":
            interactive_toxicity_chat()
        else:
            print("Usage: python test_gemini_with_tools.py [gemini|mcp|chat]")
    else:
        # Run all tests
        test_mcp_functions()
        test_toxicity_prediction()
        
        # Ask if user wants interactive chat
        response = input("\n🤔 Would you like to try interactive chat? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_toxicity_chat()

if __name__ == "__main__":
    main()