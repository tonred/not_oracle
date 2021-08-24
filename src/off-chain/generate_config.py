import json
import time

CONFIG_PATH = './off-chain/config.json'

with open(CONFIG_PATH, 'w') as f:
    json.dump(
        {
            "use_se_giver": True,
            "multisig": {
                "address": "",
                "public_key": "",
                "private_key": ""
            },
            "elector": {
                "address": "",
                "public_key": "",
                "private_key": "",
                "sign_up_start_time": int(time.time()),
                "sign_up_duration": 5,
                "validation_start_time": int(time.time()) + 10,
                "validation_duration": 1000,
                "validators_code": ""
            },
            "validator": {
                "address": "",
                "public_key": "",
                "private_key": "",
                "delay_between_quotations": 1,
                "start_balance": 30000000000,
                "treshold_to_top_up": 10000000000,
                "send_for_top_up": 20000000000
            },
            "depool": {
                "address": "",
                "public_key": "",
                "private_key": "",
            }
        }, f, indent=4
    )