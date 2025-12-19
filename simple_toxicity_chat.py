#!/usr/bin/env python3
"""
Simple Toxicity Chat
Easy-to-use interface for toxicity predictions and questions
"""
import os
from working_gemini_client import WorkingGeminiClient

def main():
    """Simple main interface"""
    print("🧪 Carbon Dot Toxicity Predictor")
    print("="*50)
    
    try:
        client = WorkingGeminiClient()
        
        print("\nWhat would you like to do?")
        print("1. Ask a question about toxicity")
        print("2. Predict toxicity for specific parameters")
        print("3. Interactive chat mode")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            question = input("\n💬 Your question: ")
            client.ask(question)
        
        elif choice == "2":
            print("\n🔬 Toxicity Prediction")
            print("Enter parameters (press Enter for defaults):")
            
            size = input("Particle size (nm) [default: 10]: ").strip()
            size = float(size) if size else 10.0
            
            zeta = input("Zeta potential (mV) [default: -20]: ").strip()
            zeta = float(zeta) if zeta else -20.0
            
            dose = input("Dose (µg/mL) [default: 50]: ").strip()
            dose = float(dose) if dose else 50.0
            
            time_h = input("Time (hours) [default: 24]: ").strip()
            time_h = float(time_h) if time_h else 24.0
            
            solvent = input("Solvent [default: Water]: ").strip()
            solvent = solvent if solvent else "Water"
            
            cell_type = input("Cell type [default: HeLa]: ").strip()
            cell_type = cell_type if cell_type else "HeLa"
            
            cell_origin = input("Cell origin [default: Human]: ").strip()
            cell_origin = cell_origin if cell_origin else "Human"
            
            client.predict_toxicity(
                particle_size=size,
                zeta_potential=zeta,
                dose=dose,
                time_hours=time_h,
                solvent=solvent,
                cell_type=cell_type,
                cell_origin=cell_origin
            )
        
        elif choice == "3":
            client.chat_loop()
        
        else:
            print("Invalid choice!")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()