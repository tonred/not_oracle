from typing import Tuple
from random import randint
from tonos_ts4 import ts4

from tonclient.client import TonClient
from .ton_contract import BasicContract, DecodedMessageBody


class NotValidatorContract(BasicContract):
    def __init__(self) -> None:
        super().__init__()
        ts4.init('../artifacts')
        self._hash_calculator = ts4.BaseContract(
            '__Calculator',
            {},
        )
        self._hashed_predictions: dict[str, Tuple[int, str]] = {}

    async def create(
        self,
        base_dir: str,
        name: str,
        client: TonClient=None,
        keypair=None,
        subscribe_event_messages=True,
    ) -> None:
        await super().create(base_dir, name, client=client, keypair=keypair, subscribe_event_messages=subscribe_event_messages)

    async def address(self) -> str:
        return await super().address({
            'notElectorArg': '0:' + '0'*64,
            'validationStartTimeArg': '2',
            'validationDurationArg': '3',
            'depoolsArg': {},
            'ownerArg': '0:' + '0'*64,
        })

    async def deploy(
        self,
        not_elector_address,
        validation_start_time,
        validation_duration,
        depools,
        owner,
    ) -> None:
        await super().deploy(args={
            'notElectorArg': not_elector_address,
            'validationStartTimeArg': validation_start_time,
            'validationDurationArg': validation_duration,
            'depoolsArg': depools,
            'ownerArg': owner,
        })

    async def _process_event(self, event: DecodedMessageBody):
        # TODO implement and process topUpMePlz events
        await super()._process_event(event)
        if event.name == 'RevealPlz':
            hashed = event.value['hashedQuotation']
            hash_key = str(int(hashed, 16))
            if hash_key in self._hashed_predictions:
                one_usd_cost, salt = self._hashed_predictions[hash_key]
                await self.reveal_quotation(one_usd_cost, salt, hash_key)

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
            },
        )

    async def set_quotation(self, one_usd_cost: int, remember_quotation=True) -> None:
        salt, hash_value = self._calc_hash(one_usd_cost)
        if remember_quotation:
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

    async def clean_up(self, destination):
        await self._call_method('cleanUp', {'destination': destination})
