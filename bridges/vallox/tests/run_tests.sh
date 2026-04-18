#!/bin/bash
# Run unit tests for vallox2mqtt

cd /Users/thomas/Projects/lares/bridges/vallox
python3 -m unittest discover -s tests -p "test_*.py"
