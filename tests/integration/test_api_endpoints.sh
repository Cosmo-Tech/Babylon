#!/bin/bash
source ../../.venv/bin/activate

set -ex

mkdir output
#timestamp=$(date +"%Y-%m-%d %H:%M:%S")

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
babylon api create-solution --organization-id $O data/solution.yaml -o output/created_sol.json
export S=$(cat output/created_sol.json | jq -r '.id')
babylon api create-workspace --organization-id $O --solution-id $S data/workspace.yaml -o output/created_ws.json
export W=$(cat output/created_ws.json | jq -r '.id')
babylon api create-dataset --organization-id $O --workspace-id $W data/dataset.yaml -o output/created_ds.json
export D=$(cat output/created_ds.json | jq -r '.id')
babylon api create-dataset-part --organization-id $O --workspace-id $W --dataset-id $D data/dataset_part.yaml -o output/created_dp.json
export DPF=$(cat output/created_dp.json | jq -r '.id')
babylon api create-dataset-part --organization-id $O --workspace-id $W --dataset-id $D data/dataset_part_db.yaml -o output/created_dp_db.json
export DPD=$(cat output/created_dp_db.json | jq -r '.id')
babylon api create-runner --organization-id $O --solution-id $S --workspace-id $W data/runner.yaml -o output/created_rn.json
export R=$(cat output/created_rn.json | jq -r '.id')
babylon api start-run --organization-id $O --workspace-id $W $R -o output/started_run.json
export RR=$(cat output/started_run.json | jq -r '.id')

# Test all the list endpoints
babylon api list-organizations
babylon api list-solutions --organization-id $O
babylon api list-workspaces --organization-id $O
babylon api list-datasets --organization-id $O --workspace-id $W
babylon api list-dataset-parts --organization-id $O --workspace-id $W --dataset-id $D
babylon api list-runners --organization-id $O --workspace-id $W
babylon api list-runs --organization-id $O --workspace-id $W $R

# Test the get endpoints
babylon api get-organization $O
babylon api get-solution --organization-id $O $S
babylon api get-workspace --organization-id $O $W
babylon api get-dataset --organization-id $O --workspace-id $W $D
babylon api get-runner --organization-id $O --workspace-id $W $R
babylon api get-run --organization-id $O --workspace-id $W --runner-id $R $RR
babylon api get-dataset-part --organization-id $O --workspace-id $W --dataset-id $D $DPF

# Test run related endpoints
babylon api get-run-status --organization-id $O --workspace-id $W --runner-id $R $RR
babylon api get-run-logs --organization-id $O --workspace-id $W --runner-id $R $RR

# Test dataset endpoints
babylon api query-data --organization-id $O --workspace-id $W --dataset-id $D --dataset-part-id $DPD --selects "tria" --limit 2 --selects "ena"

# Test update endpoints
babylon api update-organization --organization-id $O data/organization.yaml
babylon api update-solution --organization-id $O --solution-id $S data/solution.yaml
babylon api update-workspace --organization-id $O --workspace-id $W data/update_workspace.yaml
babylon api update-dataset --organization-id $O --workspace-id $W --dataset-id $D data/dataset.yaml
babylon api update-runner --organization-id $O --workspace-id $W --runner-id $R data/runner.yaml

## Clean up and test delete endpoints
babylon api delete-run --organization-id $O --workspace-id $W --runner-id $R $RR
babylon api delete-runner --organization-id $O --workspace-id $W $R
babylon api delete-dataset --organization-id $O  --workspace-id $W $D
babylon api delete-workspace  --organization-id $O $W
babylon api delete-solution  --organization-id $O $S
babylon api delete-organization $O

rm -rf ./output
rm babylon.log babylon.error