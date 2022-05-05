import asyncio
import json
import os
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
        base_dir=os.getenv('NOT_ELECTOR_PATH'),
        name=os.getenv('NOT_ELECTOR_NAME'),
        client=client,
        keypair=KeyPair(
            public=config['not_elector']['public_key'],
            secret=config['not_elector']['private_key'],
        ),
        subscribe_event_messages=False,
    )

    await asyncio.sleep(
        (config['not_elector']['sign_up_start_time'] +
            config['not_elector']['sign_up_duration']) - time.time()
    )
    await e_contract.end_election()

    # TODO check if we won election

    await asyncio.sleep(
        config['not_elector']['validation_start_time'] - time.time()
    )

    while time.time() < config['not_elector']['validation_start_time'] + config['not_elector']['validation_duration'] + 1:
        start_time = time.time()

        get_quotation_task = asyncio.create_task(get_quotation(v_contract))
        process_not_validators_events_task = asyncio.create_task(v_contract.process_events())

        _, pending = await asyncio.wait(
            (
                get_quotation_task,
                process_not_validators_events_task,
            ),
            timeout=1
        )
        delta = time.time() - start_time
        if v_contract.is_slashed:
            break
        if not pending:
            await asyncio.sleep(1 - delta)


if __name__ == '__main__':
    asyncio.run(main_loop())
