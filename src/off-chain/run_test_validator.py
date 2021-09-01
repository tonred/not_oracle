import asyncio
import json
import os
import sys
import time

from tonclient.types import KeyPair

from utils import client, send_tons_with_multisig
from contracts import ValidatorContract, DePoolMockContract


index = int(sys.argv[1])
CONFIG_PATH = './off-chain/config.json'
TEST_PATH = './off-chain/test.json'

with open(CONFIG_PATH) as f:
    config = json.load(f)

with open(TEST_PATH) as f:
    test = json.load(f)['validators'][index]


async def main_loop():
    # prepare depool
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

    # init Validator object
    v_contract = ValidatorContract()
    await v_contract.create(
        base_dir='./artifacts',
        name='Validator',
        client=client,
    )

    # send tons
    await send_tons_with_multisig(await v_contract.address(), config['validator']['start_balance'],
                                  os.path.join(os.path.dirname(__file__), '../artifacts'))

    # deploy
    await v_contract.deploy(
        elector_address=config['elector']['address'],
        validation_start_time=str(config['elector']['validation_start_time']),
        validation_duration=str(config['elector']['validation_duration']),
        depools={config['depool']['address']: True},
        owner='0:' + '0'*64,
        # TODO top_up settings
    )

    # transfer DePool stake to validator
    await d_contract.transfer_stake(
        dest=await v_contract.address(),
        amount=20000 * 10**9,
    )
    await asyncio.sleep(1)

    # sign-up
    await v_contract.sign_up()
    assert time.time() < config['elector']['sign_up_start_time'] + \
        config['elector']['sign_up_duration']

    validation_start_time = config['elector']['validation_start_time']
    for _, quotation in enumerate(test['quotations']):
        print(quotation)
        now = int(time.time())
        if now < quotation['set_quotation_time'] + validation_start_time:
            await asyncio.sleep((quotation['set_quotation_time'] + validation_start_time) - now)

        await v_contract.set_quotation(
            quotation['one_USD_cost'],
            quotation['reveal'],
        )
        await v_contract.process_events()

    if time.time() < config['elector']['validation_start_time'] + config['elector']['validation_duration']:
        await asyncio.sleep((config['elector']['validation_start_time'] + config['elector']['validation_duration']) - time.time() + 1)


if __name__ == '__main__':
    asyncio.run(main_loop())