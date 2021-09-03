#!/bin/bash


rm ./result.txt
set -e;

./compile_all.sh;

echo "Generate test"
python off-chain/generate_test.py
mv ./test.json ./off-chain/

echo "Generate config"
python off-chain/generate_config.py

echo "Deploy DePoolMock"
python off-chain/deploy_depool_mock.py

echo "Deploy not_elector"
python off-chain/deploy_not_elector.py

echo "Run!"
python off-chain/run_test_not_elector.py > /dev/null&\
    python off-chain/run_test_not_validator.py 0 > /dev/null &\
    python off-chain/run_test_not_validator.py 1 > /dev/null &\
    python off-chain/run_test_not_validator.py 2 > /dev/null &\
    python off-chain/run_test_not_validator.py 3 > /dev/null &\
    python off-chain/run_test_not_validator.py 4 > /dev/null &\
    # python off-chain/run_test_not_validator.py 5 > /dev/null &\
    # python off-chain/run_test_not_validator.py 6 > /dev/null &\
    # python off-chain/run_test_not_validator.py 7 > /dev/null &\
    # python off-chain/run_test_not_validator.py 8 > /dev/null&\
    python off-chain/run_test_not_validator.py 9 > /dev/null;