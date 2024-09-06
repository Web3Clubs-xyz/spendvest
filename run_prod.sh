#!/bin/bash

export ENVIRONMENT=production
export $(grep -v "^#" .env.production | xargs)
poetry shell
nohup python run_server.py &
pid=$!
disown $pid
echo "Spendvest is running in the background and has been disowned."
