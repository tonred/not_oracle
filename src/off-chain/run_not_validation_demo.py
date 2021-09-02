import asyncio
import json
import time

from tonclient.types import KeyPair

from utils import get_quotation, client
from contracts import NotValidatorContract, NotElectorContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main_loop():
    v_contract = NotValidatorContract()
    await v_contract.create(
        base_dir='./artifacts',
        name='NotValidator',
        client=client,
        keypair=KeyPair(
            public=config['not_validator']['public_key'],
            secret=config['not_validator']['private_key'],
        )
    )

    e_contract = NotElectorContract()
    await e_contract.create(
        base_dir='./artifacts',
        name='NotElector',
        client=client,
        keypair=KeyPair(
            public=config['not_elector']['public_key'],
            secret=config['not_elector']['private_key'],
        ),
    )

    await asyncio.sleep(
        (config['not_elector']['sign_up_start_time'] +
            config['not_elector']['sign_up_duration']) - time.time()
    )
    await e_contract.end_election()

    await asyncio.sleep(
        config['not_elector']['validation_start_time'] - time.time()
    )

    while time.time() < config['not_elector']['validation_start_time'] + config['not_elector']['validation_duration'] + 1:
        start_time = time.time()
        print('now: {}'.format(time.time() - config['not_elector']['validation_start_time']))

        get_quotation_task = asyncio.create_task(get_quotation(v_contract))
        process_not_validators_events_task = asyncio.create_task(v_contract.process_events())
        process_not_electors_events_task = asyncio.create_task(e_contract.process_events())

        _, pending = await asyncio.wait(
            (
                get_quotation_task,
                process_not_validators_events_task,
                process_not_electors_events_task,
            ),
            timeout=1
        )
        delta = time.time() - start_time
        if not pending:
            await asyncio.sleep(1 - delta)

    await asyncio.sleep(15)
    await e_contract.clean_up(config['multisig']['address'])
    await v_contract.clean_up(config['multisig']['address'])


if __name__ == '__main__':
    asyncio.run(main_loop())
