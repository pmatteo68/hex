#!/bin/bash

. ./bin/env.sh

activateVEnv() {
  echo "Activating the virtual environment (name: ${VENV_NAME})"
  source ${VENV_NAME}/bin/activate
}

if [ -d "./${VENV_NAME}" ]; then
  activateVEnv
else
  echo "Virtual environment creation ongoing (name: ${VENV_NAME})"
  python -m venv ${VENV_NAME}
  echo "Activating the virtual environment"
  activateVEnv
  echo "Installing dependencies"
  python -m pip install -r requirements.txt
  echo "Upgrading PIP"
  python -m pip install --upgrade pip
fi
echo "The environment is set."
