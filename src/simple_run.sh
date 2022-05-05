#!/bin/bash
set -e

./compile_all.sh
echo "Generate config"
python off-chain/generate_config.py

echo "Deploy DePoolMock"
python off-chain/deploy_depool_mock.py

echo "Deploy not_elector"
python off-chain/deploy_not_elector.py

echo "Deploy not_validator"
python off-chain/deploy_not_validator.py

./before_validation.sh

echo "Run validation"
python off-chain/run_not_validation_demo.py
