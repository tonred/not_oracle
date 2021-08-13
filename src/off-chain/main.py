import asyncio
import time
import logging

from utils import perform_prediction
from validator_contract import ValidatorContract
from ton_contract_example import send_grams


LOGGER = logging.getLogger(__name__)


async def main_loop():
    v_contract = ValidatorContract()
    await v_contract.create(
        dir='./artifacts',
        name='MockValidator',
    )
    await send_grams(await v_contract.address(), 10 ** 10)
    await v_contract.deploy(
        '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5',
        str(int(time.time()) + 10),
        '10',
    )

    while True:
        start_time = time.time()

        get_quotation_task = asyncio.create_task(perform_prediction(v_contract))
        process_events_task = asyncio.create_task(v_contract.process_events())

        done, _ = await asyncio.wait(
            (
                get_quotation_task,
                process_events_task
            ),
            timeout=1
        )
        delta = time.time() - start_time
        if done:
            await asyncio.sleep(1 - delta)


if __name__ == '__main__':
    asyncio.run(main_loop())
