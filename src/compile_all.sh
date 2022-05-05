#!/bin/bash
mkdir artifacts
set -e

cd contracts/not_elector
#everdev sol compile NotElector.sol
#mv NotElector.tvc ../../artifacts/
#mv NotElector.abi.json ../../artifacts/

cd ../not_validator
everdev sol compile NotValidator.sol
mv NotValidator.tvc ../../artifacts/
mv NotValidator.abi.json ../../artifacts/

cd ../depool
everdev sol compile DePoolMock.sol
mv DePoolMock.tvc ../../artifacts/
mv DePoolMock.abi.json ../../artifacts/

cd ..
everdev sol compile __Calculator.sol
mv __Calculator.tvc ../artifacts/
mv __Calculator.abi.json ../artifacts/
