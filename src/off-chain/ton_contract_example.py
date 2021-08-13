import asyncio
import json
import os

from tonclient.types import Abi, CallSet, KeyPair,\
    Signer, ParamsOfEncodeMessage, ParamsOfProcessMessage
from tonclient.types import ClientConfig
from tonclient.client import TonClient

from ton_contract import BasicContract


BASE_DIR = os.path.dirname(__file__)
GIVER_ADDRESS = '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5'
client = TonClient(config=ClientConfig(), is_async=True)


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


async def main():
    contract = BasicContract()
    await contract.create(dir='./', name='Contract')
    await send_grams(address=await contract.address(), value=10**10)
    await contract.deploy()
    result = await contract.call_method('test')

    print(f'call_method: {result}')
    print('Done')
    while True:
        await asyncio.sleep(1)
        await contract.process_events()



if __name__ == '__main__':
    asyncio.run(main())
