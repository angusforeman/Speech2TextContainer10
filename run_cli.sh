#!/bin/bash
# Load environment variables and run the CLI

cd "$(dirname "$0")"
set -a
source .env
set +a

python3 cli/cli_sdk.py "$@"
