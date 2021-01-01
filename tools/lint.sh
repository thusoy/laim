#!/bin/sh

set -e

./venv/bin/pylint --rcfile .pylintrc laim --jobs 0 --score=no
