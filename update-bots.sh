#!/bin/bash

SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

pushd $SCRIPTPATH/LEBot/
./biggus-startup.sh
popd

pushd $SCRIPTPATH/Jot/
./jot-startup.sh
popd
