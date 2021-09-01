import asyncio
import json
import os

from utils import send_tons_with_multisig, client
from contracts import NotElectorContract


CONFIG_PATH = './off-chain/config.json'


with open(CONFIG_PATH) as f:
    config = json.load(f)


async def main():
    e_contract = NotElectorContract()

    # init NotElector object
    await e_contract.create(
        base_dir='./artifacts',
        name='NotElector',
        client=client,
    )

    # send tons
    await send_tons_with_multisig(await e_contract.address(), 15 * 10 ** 9,
        os.path.join(os.path.dirname(__file__), '../artifacts')
    )

    # deploy
    await e_contract.deploy(
        config['not_elector']['sign_up_start_time'],
        config['not_elector']['sign_up_duration'],
        config['not_elector']['validation_start_time'],
        config['not_elector']['validation_duration'],
    )

    # update config
    config['not_elector']['address'] = await e_contract.address()
    config['not_elector']['public_key'] = e_contract._keypair.public
    config['not_elector']['private_key'] = e_contract._keypair.secret
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    asyncio.run(main())
