#!/bin/bash
set -e
bash compile_all.sh

set +e
python3.9 -m pytest -v -x ts4_tests
