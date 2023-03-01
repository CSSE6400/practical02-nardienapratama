#!/bin/bash
#
# Copy the tests directory and run the tests

pipenv run python3 -m unittest discover -s tests

