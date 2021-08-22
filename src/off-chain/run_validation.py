import asyncio
import json
import time

from tonclient.types import KeyPair

from utils import get_quotation, client
from validator_contract import ValidatorContract
from elector_contract import ElectorContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main_loop():
    v_contract = ValidatorContract()
    await v_contract.create(
        dir='./artifacts',
        name='Validator',
        client=client,
        keypair=KeyPair(
            public=config['validator']['public_key'],
            secret=config['validator']['private_key'],
        )
    )

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

    await asyncio.sleep(
        (config['elector']['sign_up_start_time'] +
            config['elector']['sign_up_duration']) - int(time.time()) + 1
    )
    await e_contract.end_election()

    while True:
        start_time = time.time()

        get_quotation_task = asyncio.create_task(get_quotation(v_contract))
        process_validators_events_task = asyncio.create_task(v_contract.process_events())
        process_electors_events_task = asyncio.create_task(e_contract.process_events())

        _, pending = await asyncio.wait(
            (
                get_quotation_task,
                process_validators_events_task,
                process_electors_events_task,
            ),
            timeout=1
        )
        delta = time.time() - start_time
        if not pending:
            await asyncio.sleep(1 - delta)


if __name__ == '__main__':
    asyncio.run(main_loop())
