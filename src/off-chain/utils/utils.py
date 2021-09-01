import aiohttp
import json
import os

from tonclient.types import Abi, CallSet, KeyPair, NetworkConfig,\
    Signer, ParamsOfEncodeMessage, ParamsOfProcessMessage
from tonclient.types import ClientConfig
from tonclient.client import TonClient

from contracts import ValidatorContract, MultisigContract


# BASE_DIR = os.path.dirname(__file__)
GIVER_ADDRESS = '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5'

CONFIG_PATH = './off-chain/config.json'
with open(CONFIG_PATH) as f:
    config = json.load(f)

client = TonClient(
    config=ClientConfig(
        network=NetworkConfig(
            server_address=config['network']
        )
    ),
    is_async=True,
)


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


async def send_tons_with_se_giver(
    address: str,
    value: int,
    directory: str,
):
    giver_abi = Abi.from_path(
        path=os.path.join(directory, 'GiverV2.abi.json')
    )
    call_set = CallSet(
        function_name='sendTransaction',
        input={"dest":address, "value": value, "bounce": False},
    )
    with open(os.path.join(directory, 'GiverV2.keys.json')) as json_file:
        keys = json.load(json_file)
    encode_params = ParamsOfEncodeMessage(
        abi=giver_abi, signer=Signer.Keys(KeyPair(**keys)), address=GIVER_ADDRESS,
        call_set=call_set)
    process_params = ParamsOfProcessMessage(
        message_encode_params=encode_params, send_events=False)
    await client.processing.process_message(params=process_params)

async def send_tons_with_multisig(
    address: str,
    value: int,
    directory: str,
):
    file_name = config['multisig']['file_name']
    with open(os.path.join(directory, f'{file_name}.keys.json'), 'r') as json_file:
        keys = json.load(json_file)

    multisig = MultisigContract()
    await multisig.create(
        base_dir=directory,
        name=file_name,
        client=client,
        keypair=KeyPair(
            public=keys['public'],
            secret=keys['secret'],
        )
    )
    # print('multisig address: {}'.format(
    #     await multisig.address()
    # ))

    await multisig.submit_transaction(
        dest=address,
        value=value,
    )
