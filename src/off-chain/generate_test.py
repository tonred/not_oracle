import json


CONFIG_PATH = './off-chain/config.json'

with open(CONFIG_PATH) as f:
    config = json.load(f)

test = {
    'not_validators': [{
        'quotations': [{
            'set_quotation_time': i,
            'one_USD_cost': i if j != 0 else 1,
            'reveal': True
        } for i in range(1, config['not_elector']['validation_duration'])],
        'malicious': False
    } for j in range(10)]
}

with open('test.json', 'w') as f:
    json.dump(test, f, indent=4)
