# NOT-oracle

## Как запускать?
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
Там закомментирована строчка для компиляции, можно и откомментировать если хочется.
