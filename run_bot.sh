#!/bin/bash
# this is script that runs bot

cd "$( dirname "${BASH_SOURCE[0]}" )"
source venv/bin/activate
python3 -m bot
