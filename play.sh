#!/bin/bash

. ./bin/env.sh
source ${VENV_NAME}/bin/activate

python src/main.py "$@"
