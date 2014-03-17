#!/bin/bash
# usage: source env-setup 

# When run using source as directed, $0 gets set to bash, so we must use $BASH_SOURCE
if [ -n "$BASH_SOURCE" ] ; then
    HACKING_DIR=`dirname $BASH_SOURCE`
elif [ $(basename $0) = "env-setup" ]; then
    HACKING_DIR=`dirname $0`
else
    HACKING_DIR="$PWD"
fi

# The below is an alternative to readlink -fn which doesn't exist on OS X
# Source: http://stackoverflow.com/a/1678636
FULL_PATH=`python -c "import os; print(os.path.realpath('$HACKING_DIR'))"`
PRJ_LIB="$FULL_PATH/lib"

[[ $PYTHONPATH != ${PRJ_LIB}* ]] && export PYTHONPATH=$PRJ_LIB:$PYTHONPATH
