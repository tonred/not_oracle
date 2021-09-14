# NOT-oracle

### Requirements
1. `tonos-SE >= 0.28` (if you want to launch it locally)
2. `TON-Solidity-Compiler >= 0.45.0` (We use it as `$tondev sol compile` in `compile_all.sh`, any other path to compiler's binary can be specified there). Repository also contains all necessery compiled contracts and keys for SE givers in `src/artifacts`.
3. `python >= 3.9`
4. python packages mentioned in `requirements.txt`

### How to run
Before all you just have to install requiered python packages and start tonos-SE with default settings.
```bash
cd src
python3.9 -m venv venv
source venv/bin/activate
python3.9 -m pip install -r requirements.txt

tondev se start
```

This project contains two scripts to launch NOT-Validation.

`simple_run.sh` launches only one not-elector and one not-validator with one python script listening for their events at the same time. The most lightweight and minimalistic way to launch the whole system. Here we recieve quotations from [cex.io](https://cex.io/cex-api).


`run_se_tests.sh` launches one not-elector and few not-validators as separate processes. Not-validators get quotations not from real exchange, but from some `test.json`. Simple script `generate_test.py` generates this data. Rewrite it to check any of your hypothesis:) All events emitted by not-elector are logged in `result.json`. This test is really heavy and can barely be launced with weak hardware:(


### How to tune
Look at `generate_config.py`. Network, SafeMultisig credentials, starting balances, durations, etc can be set-up there.

`config.multisig.filename` is prefix for files in `./artifacts`. For example, default value is "SafeMultisigWallet". And `src/artifacts` contains `SafeMultisigWallet.tvc`, `SafeMultisigWallet.abi.json` and `SafeMultisigWallet.keys.json`. It's credantials for buit-in tonos-SE multisig giver. But you can use your own SafeMultisig.