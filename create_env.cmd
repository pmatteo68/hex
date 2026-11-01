CALL bin\env

IF EXIST ".\%VENV_NAME%" (
  GOTO venv_exists
)

ECHO Virtual environment creation ongoing (name: %VENV_NAME%)
python -m venv %VENV_NAME%
ECHO Activating the virtual environment (name: %VENV_NAME%)
CALL %VENV_NAME%\Scripts\activate
ECHO Installing dependencies
python -m pip install -r requirements.txt
ECHO Upgrading PIP
python.exe -m pip install --upgrade pip
ECHO The virtual environment has been created (name: %VENV_NAME%)
GOTO e_end

:venv_exists
ECHO Activating the virtual environment (name: %VENV_NAME%)
CALL %VENV_NAME%\Scripts\activate

:e_end
ECHO The environment is set
