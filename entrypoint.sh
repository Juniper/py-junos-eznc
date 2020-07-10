#!/bin/bash

MSG="Valid arguments are one 'requirements.txt' file and/or one Python script"

if [  "${#@}" == 0 ]
    then
    echo "Starting an interactive Bash session"
    /bin/bash
elif [ "${#@}" == 1 ]
    then 
    case $1 in
        requirements.txt)
            echo "Installing Python packages defined in $1"
            pip install -r "$1"
            ;;
        *.py)
            echo "Executing $1 Python script"
            /usr/bin/python3 "$1"
            ;;
        *)
            echo "$MSG"
            ;;
    esac
elif [ "${#@}" == 2 ]
    then 
    case $1 in
        requirements.txt)
            echo "Installing Python packages defined in $1"
            pip install -r "$1"
            ;;
        *.py)
            echo "Executing $1 Python script"
            /usr/bin/python3 "$1"
            ;;
        *)
            echo "$MSG"
            ;;
    esac
    case $2 in
        requirements.txt)
            echo "Installing Python packages defined in $2"
            pip install -r "$2"
            ;;
        *.py)
            echo "Executing $2 Python script"
            /usr/bin/python3 "$2"
            ;;
        *)
            echo "$MSG"
            ;;
    esac
elif [ "${#@}" -gt 2 ]
    then
    echo "Only 0, 1, or 2 arguments are expected. Got ${#@}"
fi
