#!/bin/bash

set +e

## Functions
function apk_add {
    echo "Installing additional OS packages"
    while IFS= read -r pkg
        do
        echo "Installing ${pkg}"
        apk add --no-cache -q "${pkg}"
        done < "$1"
}

function pip_install {
        echo "Installing Python packages"
        pip install -r $1
}

function run_scripts {
    echo "Executing defined script"
    python3 "$1"
}

## Manually defined variables will take precedence

if [ "$APK" ]; then APK=$APK
elif [ -f "/extras/apk.txt" ]; then APK="/extras/apk.txt"
else APK=''
fi

if [ "$REQ" ]; then REQ=$REQ
elif [ -f "/extras/requirements.txt" ];then REQ="/extras/requirements.txt"
else REQ=''
fi

if [ "$1" ]; then SCRIPT=$1
else SCRIPT=''
fi

## Install extras, run scripts, or start a shell session
[[ -z "$APK" ]] || apk_add "$APK"
[[ -z "$REQ" ]] || pip_install "$REQ"
[[ -z "$SCRIPT" ]]  && /bin/bash || run_scripts "$SCRIPT"

