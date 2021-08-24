#!/bin/bash
set -e

./compile_all.sh
python off-chain/generate_config.py
python off-chain/deploy_depool_mock.py
python off-chain/deploy_elector.py
python off-chain/deploy_validator.py
python off-chain/run_validation.py
