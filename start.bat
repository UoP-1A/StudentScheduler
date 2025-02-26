@echo off
setlocal

echo Checking for virtual environment...
if not exist venv (
    echo Virtual environment not found. Creating one...
    py -m venv venv

    if errorlevel 1 (
        echo Failed to create virtual environment!
        pause
        exit /b
    )
)

echo Activating virtual environment...
call venv\Scripts\activate

:: Install/update dependencies
echo Installing/updating dependencies from requirements.txt...
pip install --upgrade -r requirements.txt || (echo Failed to install dependencies! & pause & exit /b)

:: Apply migrations only if necessary
py manage.py migrate --check > nul
if %errorlevel% neq 0 (
    echo Applying migrations...
    py manage.py migrate
) else (
    echo No migrations needed.
)

echo Running Django tests...
py manage.py test

echo Starting Django development server...
py manage.py runserver

:: Keep window open
pause
