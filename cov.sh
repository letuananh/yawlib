#!/bin/bash

python -m coverage run --source yawlib --branch -m unittest discover -s test
python -m coverage html
firefox htmlcov/index.html
