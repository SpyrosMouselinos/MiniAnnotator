#!/bin/bash


# Read the MASTER_CONFS file
source MASTER_CONFS
source ${MASTER_CONDA_ENV_BIN_PATH}/activate

# Run the PyInstaller command
pyinstaller --clean --onefile --noconsole \
    --add-data "${MASTER_CONDA_ENV_TCL_PATH};./tcl8.6" \
    --add-data "${MASTER_CONDA_ENV_TK_PATH};./tk8.6" \
    annotator.py

# Deactivate the builder environment
deactivate
