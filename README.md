# NOT-oracle

<!-- ## Как запускать?
Сейчас можно запустить, как уже писал, пару из одного валидатора и одного электора. Это делается просто из папки `src/` вызовом `launch.sh`. Чтобы сработало нужно:

1. Установить и запустить SE
```bash
tondev se start
```
2. Установить `python3.9` и все необходимые пакеты (лучше в виртуальном окружении)
```bash
python3.9 -m venv venv
source ./venv/bin/activate
python -m pip install -r requirements.txt
```
3. Запустить и радоваться)
```bash
bash launch.sh
```
Там закомментирована строчка для компиляции, можно и откомментировать если хочется. -->


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