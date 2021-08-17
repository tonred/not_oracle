import asyncio
import json

from utils import send_tons_with_se_giver,\
    send_tons_with_multisig, client
from validator_contract import ValidatorContract


CONFIG_PATH = 'validator_config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    v_contract = ValidatorContract()

    # init Validator object
    if config['debug']:
        await v_contract.create(
            dir='./artifacts',
            name='MockValidator',
            client=client,
            # TODO keys
        )
    else:
        await v_contract.create(
            dir='./artifacts',
            name='Validator',
            client=client,
        )

    # send tons
    if config['use_se_giver']:
        await send_tons_with_se_giver(await v_contract.address(), config['settings']['start_balance'])
    else:
        await send_tons_with_multisig(config['multisig'], config['settings']['start_balance'])

    # deploy
    await v_contract.deploy(
        config['elector']['address'],
        str(config['elector']['validation_start_time']),
        str(config['elector']['validation_duration']),
        # TODO top_up settings
    )

    # TODO transfer DePool stake to validator

    # sign-up
    await v_contract.sign_up()

    # update config
    config['address'] = await v_contract.address()
    with open('CONFIG_PATH', 'w') as f:
        json.dump(config, f)

if __name__ == '__main__':
    asyncio.run(main())
