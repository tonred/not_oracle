import json


CONFIG_PATH = './off-chain/config.json'

with open(CONFIG_PATH) as f:
    config = json.load(f)

test = {
    'not_validators': [{
        'quotations': [{
            'set_quotation_time': i,
            'one_USD_cost': i,
            'reveal': True
        } for i in range(config['not_elector']['validation_duration'])],
        'malicious': False
    } for i in range(10)]
}

with open('test.json', 'w') as f:
    json.dump(test, f, indent=4)
