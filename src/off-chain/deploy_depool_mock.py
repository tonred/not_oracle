import asyncio
import json
import os

from utils import send_tons_with_se_giver, client
from contracts import DePoolMockContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    d_contract = DePoolMockContract()

    # init object
    await d_contract.create(
        dir='./artifacts',
        name='DePoolMock',
        client=client,
    )

    # send tons
    await send_tons_with_se_giver(
        await d_contract.address(),
        10 ** 11,
        os.path.join(os.path.dirname(__file__), '../artifacts')
    )

    # deploy
    await d_contract.deploy()

    # update config
    config['depool']['address'] = await d_contract.address()
    config['depool']['public_key'] = d_contract._keypair.public
    config['depool']['private_key'] = d_contract._keypair.secret

    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    asyncio.run(main())
