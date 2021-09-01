from tonclient.client import TonClient
from typing import Tuple
from random import randint

from .ton_contract import BasicContract, DecodedMessageBody


class DePoolMockContract(BasicContract):
    async def create(
        self,
        base_dir: str,
        name: str,
        client: TonClient=None,
        keypair=None,
    ) -> None:
        await super().create(base_dir, name, client=client, keypair=keypair)

    async def address(self) -> str:
        return await super().address({})

    async def deploy(self) -> None:
        await super().deploy(args={})

    async def _process_event(self, event: DecodedMessageBody):
        print(' DePoolMock:')
        await super()._process_event(event)

    async def transfer_stake(
        self,
        dest,
        amount,
    ) -> None:
        await self._call_method(
            'transferStake',
            {'dest': dest, 'amount': amount},
        )

    async def clean_up(self, destination):
        await self._call_method('cleanUp', {'destination': destination})
