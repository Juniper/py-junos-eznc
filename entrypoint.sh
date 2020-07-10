#!/bin/bash

read -r -d '' USAGE << EOM

Usage:
------
0, 1, or 2 arguments are accepted.
    - If 0 arguments are given, an interactive Bash session is started.
    - If 1 argument is given, it's expected to be a Python script
      with the file suffix of .py
    - If 2 arguments are given, it's expected that the first argument will be
      a pip requirements file, named requirements.txt and the second argument
      will be a Python script with the file suffix of .py

EOM

if [  "${#@}" == 0 ]
    then
    echo -e "Starting an interactive Bash session\n"
    /bin/bash
elif [ "${#@}" == 1 ]
    then 
    case $1 in
        requirements.txt)
            echo -e "When passing 1 argument, it should only be Python script whose file name ends with .py"
            echo "$USAGE"
            exit 1
        *.py)
            echo -e "Executing $1 Python script\n"
            /usr/bin/python3 "$1"
            ;;
        *)
            echo "$USAGE"
            exit 1
            ;;
    esac
elif [ "${#@}" == 2 ]
    then 
    case $1 in
        requirements.txt)
            echo -e "Installing Python packages defined in $1\n"
            pip install -r "$1"
            ;;
        *.py)
            echo -e "When passing 2 arguments, the first argument should be a file of Python packages named requirements.txt\n"
            echo "$USAGE"
            exit 1
            ;;
        *)
            echo "$USAGE"
            exit 1
            ;;
    esac
    case $2 in
        requirements.txt)
            echo -e "When passing 2 arguments, the second argument should be a Python script ending in .py\n"
            echo "$USAGE"
            exit 1
            ;;
        *.py)
            echo -e "Executing $2 Python script\n"
            /usr/bin/python3 "$2"
            ;;
        *)
            echo "$USAGE"
            exit 1
            ;;
    esac
elif [ "${#@}" -gt 2 ]
    then
    echo -e "Only 0, 1, or 2 arguments are allowed. Got ${#@}\n"
    echo "$USAGE"
    exit 1
fi
