import asyncio
import json

from tonclient.types import KeyPair

from utils import send_tons_with_se_giver,\
    send_tons_with_multisig, client
from validator_contract import ValidatorContract
from elector_contract import ElectorContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    e_contract = ElectorContract()
    await e_contract.create(
        dir='./artifacts',
        name='Elector',
        client=client,
        keypair=KeyPair(
            public=config['elector']['public_key'],
            secret=config['elector']['private_key'],
        )
    )

    v_contract = ValidatorContract()

    # init Validator object
    await v_contract.create(
        dir='./artifacts',
        name='Validator',
        client=client,
    )

    # send tons
    if config['use_se_giver']:
        await send_tons_with_se_giver(await v_contract.address(), config['validator']['start_balance'])
    else:
        await send_tons_with_multisig(config['multisig'], config['validator']['start_balance'])

    # deploy
    await v_contract.deploy(
        config['elector']['address'],
        str(config['elector']['validation_start_time']),
        str(config['elector']['validation_duration']),
        # TODO top_up settings
    )

    # TODO transfer DePool stake to validator
    await v_contract.transfer_stake(20000 * 10**9)

    # sign-up
    await v_contract.sign_up()

    await v_contract.process_events()
    await e_contract.process_events()

    # update config
    config['validator']['address'] = await v_contract.address()
    config['validator']['public_key'] = v_contract._keypair.public
    config['validator']['private_key'] = v_contract._keypair.secret
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    asyncio.run(main())
