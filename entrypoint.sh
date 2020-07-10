#!/bin/bash

if [ -z "$1" ]
    then /bin/bash 

else 
    echo $1
    if [[ $1 == *"py" ]]
    then 
        /usr/bin/python3 "$1"
    else
        echo "Argument must be a Python file, ending in .py"
        exit 1
    fi  
fi
