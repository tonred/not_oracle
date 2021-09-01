from abc import ABC, abstractmethod
import base64
import os
import time

from typing import Callable, Any

from tonclient.types import Abi, DeploySet, CallSet, KeyPair,\
    ParamsOfDecodeMessage, ParamsOfSubscribeCollection, Signer, FunctionHeader, \
    ParamsOfEncodeMessage, ParamsOfProcessMessage, SubscriptionResponseType,\
    ResultOfSubscription, ResultOfSubscribeCollection, DecodedMessageBody
from tonclient.types import ClientConfig
from tonclient.client import TonClient, TonException


class BasicContract(ABC):
    def __init__(self) -> None:
        self._keypair = None
        self._signer = None
        self._abi = None
        self._tvc = None

        self._deploy_set = None
        self._subscriptions: dict[str, ResultOfSubscribeCollection] = {}
        self._client = None
        self._events = set()
        self._re_subscribe = False

    async def create(
        self,
        base_dir: str,
        name: str,
        *args,
        keypair: KeyPair = None,
        client: TonClient = None,
        subscribe_event_messages = True,
        **kwargs,
    ) -> None:
        if not client:
            client = TonClient(config=ClientConfig(), is_async=True)
        self._keypair = keypair or await client.crypto.generate_random_sign_keys()
        self._signer = Signer.Keys(keys=self._keypair)
        self._abi = Abi.from_path(
            path=os.path.join(base_dir, f'{name}.abi.json')
        )
        with open(os.path.join(base_dir, f'{name}.tvc'), 'rb') as file:
            self._tvc = base64.b64encode(file.read()).decode()

        self._deploy_set = DeploySet(tvc=self._tvc)
        self._client = client
        if subscribe_event_messages:
            await self._subscribe_account('boc')

    async def address(self, constructor_args_example) -> str:
        call_set = CallSet(
            function_name='constructor',
            header=FunctionHeader(pubkey=self._keypair.public),
            input=constructor_args_example,
        )
        encode_params = ParamsOfEncodeMessage(
            abi=self._abi,
            signer=self._signer,
            deploy_set=self._deploy_set,
            call_set=call_set
        )
        encoded = await self._client.abi.encode_message(params=encode_params)
        return encoded.address

    async def deploy(self, args: dict={}) -> None:
        call_set = CallSet(
            function_name='constructor',
            header=FunctionHeader(pubkey=self._keypair.public),
            input=args or None,
        )
        encode_params = ParamsOfEncodeMessage(
            abi=self._abi,
            signer=self._signer,
            deploy_set=self._deploy_set,
            call_set=call_set
        )
        process_params = ParamsOfProcessMessage(
            message_encode_params=encode_params,
            send_events=False
        )
        return await self._client.processing.process_message(
            params=process_params
        )

    async def _call_method(self, method: str, args: dict={}, callback: Callable=None) -> Any:
        call_set = CallSet(
            function_name=method,
            header=FunctionHeader(
                pubkey=self._keypair.public,
                # expire=int(time.time()) + 40,
            ),
            input=args or None,
        )
        encode_params = ParamsOfEncodeMessage(
            abi=self._abi,
            signer=self._signer,
            deploy_set=self._deploy_set,
            call_set=call_set,
        )
        process_params = ParamsOfProcessMessage(
            message_encode_params=encode_params,
            send_events=False,
        )
        try:
            return (await self._client.processing.process_message(
                params=process_params,
                callback=callback,
            )).decoded.output
        except TonException:
            return (await self._client.processing.process_message(
                params=process_params,
                callback=callback,
            )).decoded.output

    async def get(self, name: str):
        raise NotImplementedError

    async def _subscribe(
        self,
        collection: str,
        _filter: Any,
        fields: str,
        listener: Callable
    ) -> None:
        prev_subscription = self._subscriptions.get(collection)
        if prev_subscription:
            del self._subscriptions[collection]
            await self._client.net.unsubscribe(prev_subscription)

        subscription = await self._client.net.subscribe_collection(
            params=ParamsOfSubscribeCollection(
                collection,
                result=fields,
                filter=_filter
            ),
            callback=listener,
        )
        self._subscriptions[collection] = subscription

    async def _subscribe_account(
        self,
        fields: str,
    ) -> None:
        await self._subscribe(
            collection='messages',
            _filter={
                'src': {'eq': await self.address()},
                'msg_type': {'eq': 2},
            },
            fields=fields,
            listener=self._listener,
        )

    def _listener(
        self,
        response_data,
        response_type,
        *args
    ) -> None:
        if response_type == SubscriptionResponseType.OK:
            result_coro = self._decode_message(ResultOfSubscription(**response_data).result['boc'])
            self._events.add(result_coro)
        if response_type == SubscriptionResponseType.ERROR:
            print(f'oops! {response_data}')
            self._re_subscribe = True


    async def _decode_message(self, message: str):
        return await self._client.abi.decode_message(ParamsOfDecodeMessage(
            abi=self._abi,
            message=message,
        ))

    async def process_events(self):
        if self._re_subscribe:
            self._re_subscribe = False
            await self._subscribe_account('boc')
        while self._events:
            event = self._events.pop()
            res = await event
            await self._process_event(res)

    @abstractmethod
    async def _process_event(self, event: DecodedMessageBody):
        print(f'  body_type = {event.body_type}')
        print(f'  name = {event.name}')
        print(f'  value = {event.value}')
        print(f'  header = {event.header}')
