#!/bin/bash
source ../../.venv/bin/activate

set -e

# Set testing namespace
export CONTEXT="e2e"
export TENANT="sphinx"
export STATE="teststate"

babylon namespace use -c ${CONTEXT} -t ${TENANT} -s $STATE
babylon namespace get-states
babylon namespace get-contexts

# Get version
babylon api about

babylon init
babylon apply project ./output
babylon destroy