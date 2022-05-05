import json
import os

from tonclient.client import TonClient

from .ton_contract import BasicContract, DecodedMessageBody


class NotElectorContract(BasicContract):
    async def create(
        self,
        base_dir: str,
        name: str,
        client: TonClient=None,
        keypair=None,
        subscribe_event_messages = True,
    ) -> None:
        await super().create(base_dir, name, client=client, keypair=keypair, subscribe_event_messages=subscribe_event_messages)

    async def address(self) -> str:
        elector_kwargs = json.loads(os.getenv('NOT_ELECTOR_KWARGS'))
        return await super().address({
            'signUpStageBeginningArg': '0',
            'signUpStageDurationArg': '0',
            'validationStageBeginningArg': '0',
            'validationStageDurationArg': '0',
            **elector_kwargs,
        })

    async def deploy(
        self,
        signup_stage_beginning: int,
        signup_stage_duration: int,
        validation_stage_beginning: int,
        validation_stage_duration: int
    ) -> None:
        elector_kwargs = json.loads(os.getenv('NOT_ELECTOR_KWARGS'))
        await super().deploy(args={
            'signUpStageBeginningArg': str(signup_stage_beginning),
            'signUpStageDurationArg': str(signup_stage_duration),
            'validationStageBeginningArg': str(validation_stage_beginning),
            'validationStageDurationArg': str(validation_stage_duration),
            **elector_kwargs,
        })

    async def _process_event(self, event: DecodedMessageBody):
        await super()._process_event(event)

    async def end_election(self) -> None:
        await self._call_method('endElection')

    async def clean_up(self, destination):
        await self._call_method('cleanUp', {'destination': destination})
