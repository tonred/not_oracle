from tonclient.client import TonClient
from tonos_ts4 import ts4
from typing import Tuple
from random import randint

from ton_contract import BasicContract, DecodedMessageBody


class ValidatorContract(BasicContract):
    async def create(
        self,
        dir: str,
        name: str,
        client: TonClient=None,
        keypair=None,
    ) -> None:
        ts4.init('../artifacts')
        self._hash_calculator = ts4.BaseContract(
            '__Calculator',
            {},
        )
        self._hashed_predictions: dict[str, Tuple[int, str]] = {}
        await super().create(dir, name, client=client, keypair=keypair)

    async def address(self) -> str:
        return await super().address({
            'electorArg': '0:' + '0'*64,
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
        # TODO implement and process topUpMePlz events
        print(' Validator:')
        await super()._process_event(event)
        if event.name == 'RevealPlz':
            h = event.value['hashedQuotation']
            hash_key = str(int(h, 16))
            if hash_key in self._hashed_predictions:
                one_usd_cost, salt = self._hashed_predictions[hash_key]
                await self.reveal_quotation(one_usd_cost, salt, hash_key)
            else:
                raise Exception('Hash not found!')

    async def reveal_quotation(
        self,
        one_usd_cost: int,
        salt: str,
        hashed_quotation: str,
    ) -> None:
        await self._call_method(
            method='revealQuotation',
            args={
                'oneUSDCost': one_usd_cost,
                'salt': salt,
                'hashedQuotation': hashed_quotation,
            },
        )


    async def set_quotation(self, one_usd_cost: int) -> None:
        salt, hash_value = self._calc_hash(one_usd_cost)
        self._hashed_predictions[hash_value] = (one_usd_cost, salt)
        await self._call_method(
            method='setQuotation',
            args={'hashedQuotation': hash_value},
        )

    def _calc_hash(self, value: int) -> Tuple[str, str]:
        salt = randint(0, 2**256 - 1)
        res = self._hash_calculator.call_method(
            'calc',
            {'value': value, 'salt': salt},
        )
        return str(salt), str(res)

    async def sign_up(self):
        await self._call_method('signUp')

    async def transfer_stake(self, value: int) -> None:
        await self._call_method(
            method='onStakeTransfered',
            args={'stakeSizeArg': value},
        )
