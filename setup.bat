@echo off
REM FDA PharmaVigilance - Complete Setup Script for Windows

echo.
echo ================================
echo FDA PharmaVigilance Setup
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.11+
    exit /b 1
)
echo Python version:
python --version
echo.

REM Create .env file
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit with your credentials:
    echo   - SNOWFLAKE_ACCOUNT
    echo   - SNOWFLAKE_USER
    echo   - SNOWFLAKE_PASSWORD
    echo   - FDA_API_KEY
    echo.
    pause
)
echo Environment configured
echo.

REM Setup Ingestion Layer
echo Setting up Ingestion Layer...
cd ingestion
pip install -r requirements.txt
if not exist logs mkdir logs
if not exist data\sample mkdir data\sample
if not exist data\mappings mkdir data\mappings
cd ..
echo Ingestion layer ready
echo.

REM Setup dbt
echo Setting up dbt...
cd dbt
pip install -r requirements.txt
cd ..
echo dbt ready
echo.

REM Setup Streamlit
echo Setting up Streamlit...
cd streamlit
pip install -r requirements.txt
if not exist .streamlit (
    mkdir .streamlit
)
if not exist .streamlit\secrets.toml (
    copy .streamlit\secrets.toml.example .streamlit\secrets.toml
    echo Created .streamlit/secrets.toml. Please edit with your credentials.
)
cd ..
echo Streamlit ready
echo.

echo ================================
echo Setup Complete!
echo ================================
echo.
echo Next steps:
echo.
echo 1. Run ingestion:
echo    cd ingestion
echo    python src/main.py
echo.
echo 2. Run dbt transformations:
echo    cd dbt
echo    dbt run
echo.
echo 3. Run Streamlit dashboard:
echo    cd streamlit
echo    streamlit run app.py
echo.
echo Or use Docker:
echo    docker-compose up
echo.
