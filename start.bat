@echo off
echo ============================================================
echo Carbon Dot Toxicity Prediction API
echo ============================================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create a .env file with your Gemini API key:
    echo API_KEY=your_api_key_here
    echo.
    pause
    exit /b 1
)

REM Check if models exist
if not exist best_model_without_family.pkl (
    echo ERROR: Model files not found!
    echo Please copy all 4 PKL files to the Backend folder
    echo.
    pause
    exit /b 1
)

echo Starting server...
echo Server will be available at: http://localhost:8000
echo Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

python test.py

