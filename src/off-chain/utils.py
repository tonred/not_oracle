import aiohttp
import json

from validator_contract import ValidatorContract


async def perform_prediction(contract: ValidatorContract):
    # TODO implement session-pool
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://cex.io/api/convert/TON/USD',
            data={"amnt": 1},
        ) as resp:
            # print(f'status: {resp.status}')
            text = await resp.text()
            res = json.loads(text)['amnt']
            # print(f'1 USD = {round((1/res) * 10**9)} nanoTON\n')

            await contract.set_quotation(round((1/res) * 10**9))
