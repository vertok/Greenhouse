#!/bin/bash

echo "installing virtualenv if not exists already..." ;
python -m virtualenv .venv;

echo "activating virtualenv..." ;
source .venv/Scripts/activate ;

echo "updating pip module..." ;
python -m pip install pip --upgrade ;

echo "installing required python libraries..." ;
.venv/Scripts/python -m pip install -r requirements.txt ;

echo "Virtual environment setup complete." \
"Please activate it via:" \
".//.venv//Scripts//activate under Windows" \
"(or source .venv/bin/activate under Unix)" 
