"""
Test client for the toxicity prediction API
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_api(message):
    """Send a test message to the API"""
    print(f"\n{'='*70}")
    print(f"USER: {message}")
    print(f"{'='*70}")
    
    response = requests.post(
        f"{API_URL}/message",
        json={"text": message}
    )
    
    result = response.json()
    
    if result.get("success"):
        print(f"\nASSISTANT: {result['text']}")
        
        if result.get("tool_calls"):
            print(f"\n{'─'*70}")
            print(f"Tool Calls Made: {len(result['tool_calls'])}")
            print(f"{'─'*70}")
            for i, tool_call in enumerate(result['tool_calls'], 1):
                print(f"\n[{i}] Function: {tool_call['function']}")
                print(f"    Arguments: {json.dumps(tool_call['arguments'], indent=6)}")
                if tool_call['result'].get('success'):
                    print(f"    ✓ Result: {tool_call['result'].get('class_label', 'N/A')}")
                    if 'probability_toxic' in tool_call['result']:
                        print(f"    Probability (Toxic): {tool_call['result']['probability_toxic']:.3f}")
                else:
                    print(f"    ✗ Error: {tool_call['result'].get('error', 'Unknown')}")
    else:
        print(f"\n✗ ERROR: {result.get('text', 'Unknown error')}")
    
    print(f"\n{'='*70}\n")
    return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Toxicity Prediction API - Test Client")
    print("="*70)
    
    # Check health
    try:
        health = requests.get(f"{API_URL}/health").json()
        print(f"✓ API Status: {health['status']}")
        print(f"✓ Models Loaded: {health['models_loaded']}")
        print(f"✓ Tools Available: {len(health['tools_available'])}")
    except Exception as e:
        print(f"✗ Error connecting to API: {e}")
        print("Make sure the server is running: python test.py")
        exit(1)
    
    # Test 1: Ask about toxicity with all parameters
    print("\n" + "="*70)
    print("TEST 1: Prediction Request (All Parameters)")
    print("="*70)
    
    test_api(
        "Is a 7.5nm carbon dot toxic at 15 µg/mL for 24 hours? "
        "ZetaPotential is -22.0 mV, extracted with Ethanol, "
        "tested on HeLa cells from Human origin."
    )
    
    # Test 2: Ask for explanation
    print("\n" + "="*70)
    print("TEST 2: Explanation Request")
    print("="*70)
    
    test_api(
        "Explain why a 10nm carbon dot at 50 µg/mL for 48 hours would be toxic. "
        "ZetaPotential: -15 mV, Solvent: Water, CellType: MCF7, CellOrigin: Human."
    )
    
    # Test 3: Missing parameters (should ask for them)
    print("\n" + "="*70)
    print("TEST 3: Incomplete Parameters")
    print("="*70)
    
    test_api(
        "Is a 5nm carbon dot toxic at 20 µg/mL?"
    )
    
    # Test 4: With plant family
    print("\n" + "="*70)
    print("TEST 4: Prediction with Plant Family")
    print("="*70)
    
    test_api(
        "Predict toxicity: ParticleSize=8nm, ZetaPotential=-18mV, Dose=25µg/mL, "
        "Time=36h, Family=Fabaceae, Solvent=Ethanol, CellType=A549, CellOrigin=Human"
    )
    
    print("\n" + "="*70)
    print("All Tests Complete!")
    print("="*70)

