import asyncio
import time

from utils import get_quotation, send_grams, client
from validator_contract import ValidatorContract


async def main_loop():
    v_contract = ValidatorContract()
    await v_contract.create(
        dir='./artifacts',
        name='MockValidator',
        client=client,
    )
    await send_grams(await v_contract.address(), 10 ** 10)
    await v_contract.deploy(
        '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5',
        str(int(time.time()) + 10),
        '10',
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
