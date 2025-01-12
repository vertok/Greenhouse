#!/bin/bash

echo "Installing and updating python pip, virtualenv..."
python -m pip install pip virtualenv --upgrade ;

echo "Determine the operating system"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]]; then
    OS="cygwin"
elif [[ "$OSTYPE" == "msys" ]]; then
    OS="msys"
elif [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
  echo "Unsupported operating system."
  exit 1
fi

echo "Activating virtual enviroment..." ;
python -m virtualenv .venv ;

echo "Installing python pip, build module for building the package in .venv..." ;
python -m pip install build --upgrade ;

echo "Virtual environment setup complete." \
"Please activate it via:" \
".//.venv//Scripts//activate under Windows" \
"(or source .venv/bin/activate under Unix)" 
