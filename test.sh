#!/usr/bin/sh

echo "Test YAWLib"
# Alternative: test a specific file
# python -m unittest test.test_demolib
python3 -m unittest discover -s ./test
