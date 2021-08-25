from tonclient.client import TonClient
from typing import Tuple
from random import randint

from .ton_contract import BasicContract, DecodedMessageBody


class ElectorContract(BasicContract):
    async def create(
        self,
        dir: str,
        name: str,
        client: TonClient=None,
        keypair=None,
    ) -> None:
        await super().create(dir, name, client=client, keypair=keypair)

    async def address(self) -> str:
        return await super().address({
            'signUpStageBeginningArg': '0',
            'signUpStageDurationArg': '0',
            'validationStageBeginningArg': '0',
            'validationStageDurationArg': '0',
            'validatorsCodeArg': '',
        })

    async def deploy(
        self,
        signup_stage_beginning: int,
        signup_stage_duration: int,
        validation_stage_beginning: int,
        validation_stage_duration: int,
        validators_code: str,
    ) -> None:
        await super().deploy(args={
            'signUpStageBeginningArg': str(signup_stage_beginning),
            'signUpStageDurationArg': str(signup_stage_duration),
            'validationStageBeginningArg': str(validation_stage_beginning),
            'validationStageDurationArg': str(validation_stage_duration),
            'validatorsCodeArg': validators_code,
        })

    async def _process_event(self, event: DecodedMessageBody):
        print(' Elector:')
        await super()._process_event(event)

    async def end_election(self) -> None:
        await self._call_method('endElection')
