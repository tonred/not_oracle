import asyncio
import time

from utils import get_quotation, client
from validator_contract import ValidatorContract


async def main_loop():
    v_contract = ValidatorContract()
    await v_contract.create(
        dir='./artifacts',
        name='Validator',
        client=client,
    )

    while True:
        start_time = time.time()

        get_quotation_task = asyncio.create_task(get_quotation(v_contract))
        process_events_task = asyncio.create_task(v_contract.process_events())

        _, pending = await asyncio.wait(
            (
                get_quotation_task,
                process_events_task
            ),
            timeout=1
        )
        delta = time.time() - start_time
        if not pending:
            await asyncio.sleep(1 - delta)


if __name__ == '__main__':
    asyncio.run(main_loop())
