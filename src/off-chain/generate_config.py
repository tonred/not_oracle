import json
import time

CONFIG_PATH = './off-chain/config.json'

with open(CONFIG_PATH, 'w') as f:
    json.dump(
        {
            # "network": r"https://net.ton.dev",
            # "multisig": {
            #     "address": "0:4015f67493f1b53afde587eaa1dd8d6af88665b817e231130b1582018548b5f8",
            #     "file_name": "SafeMultisigWalletDev",
            # },
            "network": r"http://localhost",
            "multisig": {
                "address": "0:d5f5cfc4b52d2eb1bd9d3a8e51707872c7ce0c174facddd0e06ae5ffd17d2fcd",
                "file_name": "SafeMultisigWallet",
            },
            "not_elector": {
                "address": "",
                "public_key": "",
                "private_key": "",
                "sign_up_start_time": int(time.time()),

                "sign_up_duration": 30,
                "validation_start_time": int(time.time()) + 45,
                "validation_duration": 120,

                # "sign_up_duration": 90,
                # "validation_start_time": int(time.time()) + 100,
                # "validation_duration": 180,
            },
            "not_validator": {
                "address": "",
                "public_key": "",
                "private_key": "",
                "delay_between_quotations": 1,
                "start_balance": 30 * 10**9,
                "treshold_to_top_up": 5 * 10**9,
                "send_for_top_up": 10 * 10**9
            },
            "depool": {
                "address": "",
                "public_key": "",
                "private_key": "",
            }
        }, f, indent=4
    )
