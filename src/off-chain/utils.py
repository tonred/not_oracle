import aiohttp
import json
import os

from tonclient.types import Abi, CallSet, KeyPair,\
    Signer, ParamsOfEncodeMessage, ParamsOfProcessMessage
from tonclient.types import ClientConfig
from tonclient.client import TonClient

from validator_contract import ValidatorContract


BASE_DIR = os.path.dirname(__file__)
GIVER_ADDRESS = '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5'
client = TonClient(config=ClientConfig(), is_async=True)


async def get_quotation(contract: ValidatorContract):
    # TODO implement session-pool
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://cex.io/api/convert/TON/USD',
            data={"amnt": 1},
        ) as resp:
            text = await resp.text()
            res = json.loads(text)['amnt']

            await contract.set_quotation(round((1/res) * 10**9))


async def send_grams(address: str, value: int):
    giver_abi = Abi.from_path(
        path=os.path.join(BASE_DIR, '../artifacts/GiverV2.abi.json'))
    call_set = CallSet(
        function_name='sendTransaction',
        input={"dest":address, "value": value, "bounce": False},
    )
    with open(os.path.join(BASE_DIR, '../artifacts/GiverV2.keys.json')) as json_file:
        keys = json.load(json_file)
    encode_params = ParamsOfEncodeMessage(
        abi=giver_abi, signer=Signer.Keys(KeyPair(**keys)), address=GIVER_ADDRESS,
        call_set=call_set)
    process_params = ParamsOfProcessMessage(
        message_encode_params=encode_params, send_events=False)
    await client.processing.process_message(params=process_params)
