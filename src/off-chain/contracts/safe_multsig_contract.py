from tonclient.client import TonClient
from tonclient.types import DecodedMessageBody, KeyPair
from .ton_contract import BasicContract

class MultisigContract(BasicContract):
    async def create(self, base_dir: str, name: str, *args, keypair: KeyPair, client: TonClient, **kwargs) -> None:
        return await super().create(base_dir, name, *args, keypair=keypair, client=client, subscribe_event_messages=False, **kwargs)

    async def _process_event(self, event: DecodedMessageBody):
        raise NotImplementedError

    async def submit_transaction(
        self,
        dest,
        value,
        bounce = False,
        all_balance = False,
        payload = '',
    ):
        return await self._call_method(
            method='submitTransaction',
            args={
                'dest': dest,
                'value': value,
                'bounce': bounce,
                'allBalance': all_balance,
                'payload': payload
            }
        )
    async def address(self):
        return await super().address({
            'owners': [], 'reqConfirms': 0
        })
