#!/bin/bash
set -e

./compile_all.sh
echo "Generate config"
python off-chain/generate_config.py

echo "Deploy DePoolMock"
python off-chain/deploy_depool_mock.py

echo "Deploy elector"
python off-chain/deploy_elector.py

echo "Deploy validator"
python off-chain/deploy_validator.py

echo "Run validation"
python off-chain/run_validation.py
