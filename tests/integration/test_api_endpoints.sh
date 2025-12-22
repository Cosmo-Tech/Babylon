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

babylon api create-organization data/organization.yaml -o output/created_org.json
export O=$(cat output/created_org.json | jq -r '.id')
babylon api create-solution --oid $O data/solution.yaml -o output/created_sol.json
export S=$(cat output/created_sol.json | jq -r '.id')
babylon api create-workspace --oid $O --sid $S data/workspace.yaml -o output/created_ws.json
export W=$(cat output/created_ws.json | jq -r '.id')
babylon api create-dataset --oid $O --wid $W data/dataset.yaml -o output/created_ds.json
export D=$(cat output/created_ds.json | jq -r '.id')
babylon api create-dataset-part --oid $O --wid $W --did $D data/dataset_part.yaml -o output/created_dp.json
export DPF=$(cat output/created_dp.json | jq -r '.id')
babylon api create-dataset-part --oid $O --wid $W --did $D data/dataset_part_db.yaml -o output/created_dp_db.json
export DPD=$(cat output/created_dp_db.json | jq -r '.id')
babylon api create-runner --oid $O --sid $S --wid $W data/runner.yaml -o output/created_rn.json
export R=$(cat output/created_rn.json | jq -r '.id')
babylon api start-run --oid $O --wid $W --rid $R -o output/started_run.json
export RR=$(cat output/started_run.json | jq -r '.id')

# Test all the list endpoints
babylon api list-organizations
babylon api list-solutions --oid $O
babylon api list-workspaces --oid $O
babylon api list-datasets --oid $O --wid $W
babylon api list-dataset-parts --oid $O --wid $W --did $D
babylon api list-runners --oid $O --wid $W
babylon api list-runs --oid $O --wid $W --rid $R

# Test the get endpoints
babylon api get-organization --oid $O
babylon api get-solution --oid $O --sid $S
babylon api get-workspace --oid $O --wid $W
babylon api get-dataset --oid $O --wid $W --did $D
babylon api get-runner --oid $O --wid $W --rid $R
babylon api get-run --oid $O --wid $W --rid $R --rnid $RR
babylon api get-dataset-part --oid $O --wid $W --did $D --dpid $DPF

# Test run related endpoints
babylon api get-run-status --oid $O --wid $W --rid $R --rnid $RR
babylon api get-run-logs --oid $O --wid $W --rid $R --rnid $RR

# Test dataset endpoints
babylon api query-data --oid $O --wid $W --did $D --dpid $DPD --selects "tria" --limit 2 --selects "ena"

# Test update endpoints
babylon api update-organization --oid $O data/organization.yaml
babylon api update-solution --oid $O --sid $S data/solution.yaml
babylon api update-workspace --oid $O --wid $W data/update_workspace.yaml
babylon api update-dataset --oid $O --wid $W --did $D data/dataset.yaml
babylon api update-runner --oid $O --wid $W --rid $R data/runner.yaml

## Clean up and test delete endpoints
babylon api delete-run --oid $O --wid $W --rid $R --rnid $RR
babylon api delete-runner --oid $O --wid $W --rid $R
babylon api delete-dataset --oid $O --wid $W --did $D
babylon api delete-workspace --oid $O --wid $W
babylon api delete-solution --oid $O --sid $S
babylon api delete-organization --oid $O

rm -rf ./output
rm babylon.log babylon.error