@echo off

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

for /f "delims=. tokens=1,2,3" %%a in ('python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"') do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
    set PYTHON_PATCH=%%c
)

if "%PYTHON_MAJOR%"=="" (
    echo Failed to get Python version.
    pause
    exit /b 1
)

if %PYTHON_MAJOR% LSS 3 (
    echo Python version must be at least 3.12. Current version: %PYTHON_MAJOR%.%PYTHON_MINOR%.%PYTHON_PATCH%
    pause
    exit /b 1
)
if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 12 (
    echo Python version must be at least 3.12. Current version: %PYTHON_MAJOR%.%PYTHON_MINOR%.%PYTHON_PATCH%
    pause
    exit /b 1
)

set VENV_DIR=.venv
set NEW_ENV=0

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found, creating a new one...

    python -m venv %VENV_DIR%
    
    if not exist "%VENV_DIR%\Scripts\activate.bat" (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )

    echo Virtual environment created.
    set NEW_ENV=1
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

if "%NEW_ENV%"=="1" (
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
)

echo Running the application...
python main.py

deactivate

echo Application finished.
pause
