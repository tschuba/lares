#!/bin/bash
# Run unit tests for sungrow2mqtt

cd /Users/thomas/Projects/lares/bridges/sungrow2mqtt/tests/unit
python3 -m unittest discover -p "test_*.py"
