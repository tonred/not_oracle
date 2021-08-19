#!/bin/bash
mkdir artifacts
set -e

cd contracts/elector
tondev sol compile Elector.sol
mv Elector.tvc ../../artifacts/
mv Elector.abi.json ../../artifacts/

cd ../validator
tondev sol compile Validator.sol
mv Validator.tvc ../../artifacts/
mv Validator.abi.json ../../artifacts/

tondev sol compile MockValidator.sol
mv MockValidator.tvc ../../artifacts/
mv MockValidator.abi.json ../../artifacts/

cd ..
tondev sol compile __Calculator.sol
mv __Calculator.tvc ../artifacts/
mv __Calculator.abi.json ../artifacts/
