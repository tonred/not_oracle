import asyncio
import json
import os
import time

from tonclient.types import KeyPair

from utils import get_quotation, client
from contracts import NotValidatorContract, NotElectorContract


CONFIG_PATH = './off-chain/config.json'


class LoggingNotElector(NotElectorContract):
    async def _process_event(self, event):
        if event.name in ('oneUSDCostCalculatedEvent', 'oneUSDCostCalculationStarted'):
            event.value['time'] = int(event.value['time'], 16)
        print({
            'name': event.name,
            'value': event.value
        })
        await super()._process_event(event)


class LoggingNotValidator(NotValidatorContract):
    async def _process_event(self, event):
        if event.name in ('oneUSDCostCalculatedEvent', 'oneUSDCostCalculationStarted'):
            event.value['time'] = int(event.value['time'], 16)
        print({
            'name': event.name,
            'value': event.value
        })
        await super()._process_event(event)


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main_loop():
    v_contract = LoggingNotValidator()
    await v_contract.create(
        base_dir='./artifacts',
        name='NotValidator',
        client=client,
        keypair=KeyPair(
            public=config['not_validator']['public_key'],
            secret=config['not_validator']['private_key'],
        )
    )

    e_contract = LoggingNotElector()
    await e_contract.create(
        base_dir=os.getenv('NOT_ELECTOR_PATH'),
        name=os.getenv('NOT_ELECTOR_NAME'),
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
    # await e_contract.clean_up(config['multisig']['address'])  // added


if __name__ == '__main__':
    asyncio.run(main_loop())
