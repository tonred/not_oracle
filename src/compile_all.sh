#!/bin/bash
mkdir artifacts
set -e

cd contracts/not_elector
tondev sol compile NotElector.sol
mv NotElector.tvc ../../artifacts/
mv NotElector.abi.json ../../artifacts/

cd ../not_validator
tondev sol compile NotValidator.sol
mv NotValidator.tvc ../../artifacts/
mv NotValidator.abi.json ../../artifacts/

cd ../depool
tondev sol compile DePoolMock.sol
mv DePoolMock.tvc ../../artifacts/
mv DePoolMock.abi.json ../../artifacts/

cd ..
tondev sol compile __Calculator.sol
mv __Calculator.tvc ../artifacts/
mv __Calculator.abi.json ../artifacts/
