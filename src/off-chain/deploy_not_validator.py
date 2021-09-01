import asyncio
import json
import os

from tonclient.types import KeyPair

from utils import send_tons_with_se_giver,\
    send_tons_with_multisig, client
from contracts import NotValidatorContract, NotElectorContract, DePoolMockContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    # prepare not_elector and depool
    e_contract = NotElectorContract()
    await e_contract.create(
        base_dir='./artifacts',
        name='NotElector',
        client=client,
        keypair=KeyPair(
            public=config['not_elector']['public_key'],
            secret=config['not_elector']['private_key'],
        ),
        subscribe_event_messages=False,
    )

    d_contract = DePoolMockContract()
    await d_contract.create(
        base_dir='./artifacts',
        name='DePoolMock',
        client=client,
        keypair=KeyPair(
            public=config['depool']['public_key'],
            secret=config['depool']['private_key'],
        )
    )

    # init NotValidator object
    v_contract = NotValidatorContract()
    await v_contract.create(
        base_dir='./artifacts',
        name='NotValidator',
        client=client,
        subscribe_event_messages=False,
    )

    # send tons
    await send_tons_with_multisig(
    # await send_tons_with_se_giver(
        await v_contract.address(),
        config['not_validator']['start_balance'],
        os.path.join(os.path.dirname(__file__), '../artifacts')
    )

    # deploy
    await v_contract.deploy(
        not_elector_address=config['not_elector']['address'],
        validation_start_time=str(config['not_elector']['validation_start_time']),
        validation_duration=str(config['not_elector']['validation_duration']),
        depools={config['depool']['address']: True},
        owner='0:' + '0'*64,
        # TODO top_up settings
    )

    # TODO transfer DePool stake to not_validator
    await d_contract.transfer_stake(
        dest=await v_contract.address(),
        amount=20000 * 10**9,
    )
    await asyncio.sleep(1)

    # sign-up
    await v_contract.sign_up()
    await d_contract.clean_up(config['multisig']['address'])

    # update config
    config['not_validator']['address'] = await v_contract.address()
    config['not_validator']['public_key'] = v_contract._keypair.public
    config['not_validator']['private_key'] = v_contract._keypair.secret
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    asyncio.run(main())
