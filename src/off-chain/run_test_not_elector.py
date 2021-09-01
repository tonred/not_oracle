import asyncio
import json
import os
import time
from typing import List

from tonclient.types import DecodedMessageBody, KeyPair

from utils import client
from contracts import NotElectorContract


CONFIG_PATH = './off-chain/config.json'
events: List[DecodedMessageBody] = []


class LoggingNotElector(NotElectorContract):
    async def _process_event(self, event: DecodedMessageBody):
        if event.name == 'oneUSDCostCalculatedEvent':
            event.value['time'] = int(event.value['time'], 16)
        events.append({
            'name': event.name,
            'value': event.value
        })
        await super()._process_event(event)


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    e_contract = LoggingNotElector()

    await e_contract.create(
        base_dir='./artifacts',
        name='NotElector',
        client=client,
        keypair=KeyPair(
            public=config['not_elector']['public_key'],
            secret=config['not_elector']['private_key'],
        )
    )

    await asyncio.sleep(
        (config['not_elector']['sign_up_start_time'] +
            config['not_elector']['sign_up_duration']) - int(time.time()) + 1
    )
    await e_contract.end_election()
    await asyncio.sleep(
        (config['not_elector']['validation_start_time']) - time.time() + 0.1
    )

    while time.time() < config['not_elector']['validation_start_time'] + config['not_elector']['validation_duration'] + 1:
        start_time = time.time()
        print('now: {}'.format(start_time - config['not_elector']['validation_start_time']))

        process_not_electors_events_task = asyncio.create_task(e_contract.process_events())

        _, pending = await asyncio.wait(
            (process_not_electors_events_task,),
            timeout=1
        )
        delta = time.time() - start_time
        if not pending:
            await asyncio.sleep(1 - delta)

    print('All!')
    await e_contract.process_events()
    with open('result.json', 'w') as file:
        json.dump(events, file, indent=4)


if __name__ == '__main__':
    asyncio.run(main())
