#!/bin/bash

coverage run --source yawlib --branch -m unittest discover -s test
coverage html
firefox htmlcov/index.html
