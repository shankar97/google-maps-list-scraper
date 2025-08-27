#!/bin/bash

cd <relative_path_to_your_project_directory>
python -m venv map-env
source map-env/bin/activate
pip install -r requirements.txt
python main.py