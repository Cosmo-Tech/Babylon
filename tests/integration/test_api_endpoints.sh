#!/usr/bin/env bash

set -e

if [ -f "../../.venv/Scripts/activate" ]; then
    . ../../.venv/Scripts/activate
  else
    . ../../.venv/bin/activate
fi

mkdir output

# Set testing namespace
export CONTEXT="integration"
export TENANT="sphinx"
export STATE="teststate"

babylon namespace use -c ${CONTEXT} -t ${TENANT} -s $STATE
babylon namespace get-states
babylon namespace get-contexts

# Get version
babylon api about

# Create an organization, solution, workspace, dataset,runner and start a run

babylon api organizations create data/organization.yaml -f output/created_org.json
export O=$(cat output/created_org.json | jq -r '.id')
babylon api solutions create --oid $O data/solution.yaml -f output/created_sol.json
export S=$(cat output/created_sol.json | jq -r '.id')
babylon api workspaces create --oid $O --sid $S data/workspace.yaml -f output/created_ws.json
export W=$(cat output/created_ws.json | jq -r '.id')
babylon api datasets create --oid $O --wid $W data/dataset.yaml -f output/created_ds.json
export D=$(cat output/created_ds.json | jq -r '.id')
babylon api datasets create-part --oid $O --wid $W --did $D data/dataset_part.yaml -f output/created_dp.json
export DPF=$(cat output/created_dp.json | jq -r '.id')
babylon api datasets create-part --oid $O --wid $W --did $D data/dataset_part_db.yaml -f output/created_dp_db.json
export DPD=$(cat output/created_dp_db.json | jq -r '.id')
babylon api runners create --oid $O --sid $S --wid $W data/runner.yaml -f output/created_rn.json
export R=$(cat output/created_rn.json | jq -r '.id')
babylon api runners start --oid $O --wid $W --rid $R -f output/started_run.json
export RR=$(cat output/started_run.json | jq -r '.id')

# Test all the list endpoints
babylon api organizations list
babylon api solutions list --oid $O
babylon api workspaces list --oid $O
babylon api datasets list --oid $O --wid $W
babylon api datasets list-parts --oid $O --wid $W --did $D
babylon api runners list --oid $O --wid $W
babylon api runs list --oid $O --wid $W --rid $R

# Test output format 
babylon api organizations list -o wide

# Test the get endpoints
babylon api organizations get --oid $O
babylon api organizations get --oid $O -o json
babylon api solutions get --oid $O --sid $S
babylon api solutions get --oid $O --sid $S -o yaml
babylon api workspaces get --oid $O --wid $W
babylon api datasets get --oid $O --wid $W --did $D
babylon api runners get --oid $O --wid $W --rid $R
babylon api runs get --oid $O --wid $W --rid $R --rnid $RR
babylon api datasets get-part --oid $O --wid $W --did $D --dpid $DPF

# Test run related endpoints
babylon api runs get-status --oid $O --wid $W --rid $R --rnid $RR
babylon api runs get-logs --oid $O --wid $W --rid $R --rnid $RR

# Test dataset endpoints
babylon api datasets query-data --oid $O --wid $W --did $D --dpid $DPD --selects "tria" --limit 2 --selects "ena"

# Test update endpoints
babylon api organizations update --oid $O data/organization.yaml
babylon api solutions update --oid $O --sid $S data/solution.yaml
babylon api workspaces update --oid $O --wid $W data/update_workspace.yaml
babylon api datasets update --oid $O --wid $W --did $D data/dataset.yaml
babylon api runners update --oid $O --wid $W --rid $R data/runner.yaml

## Clean up and test delete endpoints
babylon api runs delete --oid $O --wid $W --rid $R --rnid $RR
babylon api runners delete --oid $O --wid $W --rid $R
babylon api datasets delete --oid $O --wid $W --did $D
babylon api workspaces delete --oid $O --wid $W
babylon api solutions delete --oid $O --sid $S
babylon api organizations delete --oid $O

rm -rf ./output
rm babylon_error.log babylon_info.log