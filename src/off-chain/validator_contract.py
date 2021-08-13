from tonclient.types import SubscriptionResponseType
from tonos_ts4 import ts4
from typing import Tuple
from random import randint

from ton_contract import BasicContract, CallSet, FunctionHeader, ParamsOfEncodeMessage, DecodedMessageBody


class ValidatorContract(BasicContract):
    async def create(
        self,
        dir: str,
        name: str
    ) -> None:
        ts4.init('../artifacts')
        self._hash_calculator = ts4.BaseContract(
            '__Calculator',
            {}
        )
        self._hashed_predictions = {}
        await super().create(dir, name)

    async def address(self) -> str:
        return await super().address({
            'electorArg': '0:b5e9240fc2d2f1ff8cbb1d1dee7fb7cae155e5f6320e585fcc685698994a19a5',
            'validationStartTimeArg': '2',
            'validationDurationArg': '3',
        })

    async def deploy(self, elector_address, validation_start_time, validation_duration) -> None:
        await super().deploy(args={
            'electorArg': elector_address,
            'validationStartTimeArg': validation_start_time,
            'validationDurationArg': validation_duration,
        })

    async def _process_event(self, event: DecodedMessageBody):
        await super()._process_event(event)
        if event.name == 'RevealPlz':
            h = event.value['hashedQuotation']
            print(int(h, 16))
        # print(f'  body_type = {event.body_type}')
        # print(f'  name = {event.name}')
        # print(f'  value = {event.value}')
        # print(f'  header = {event.header}')


    async def set_quotation(self, one_usd_cost: int) -> None:
        salt, hash_value = self._calc_hash(one_usd_cost)
        self._hashed_predictions[hash_value] = (one_usd_cost, salt)
        await self.call_method(
            method='setQuotation',
            args={'hashedQuotation': hash_value}
        )

    def _calc_hash(self, value: int) -> Tuple[str, str]:
        salt = randint(0, 2**256 - 1)
        res = self._hash_calculator.call_method(
            'calc',
            {'value': value, 'salt': salt},
        )
        print(value, salt, res)
        return str(salt), str(res)
