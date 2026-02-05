#!/usr/bin/env bash

set -e

if [ -f "../../.venv/Scripts/activate" ]; then
    . ../../.venv/Scripts/activate
  else
    . ../../.venv/bin/activate
fi

# Set testing namespace
export CONTEXT="e2e"
export TENANT="sphinx"
export STATE="teststate"

babylon namespace use -c ${CONTEXT} -t ${TENANT} -s $STATE
babylon namespace get-states local
babylon namespace get-contexts

# Get version
babylon api about

babylon init
babylon apply --exclude webapp project
babylon destroy