from aiogram import types, Dispatcher
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import Throttled


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple middleware
    """

    def __init__(
            self,
            limit: float = DEFAULT_RATE_LIMIT,
            key_prefix: str = 'antiflood_'
    ):
        self.rate_limit = limit
        self.prefix = key_prefix

        super().__init__()

    # noinspection PyUnusedLocal
    async def on_process_message(self, message: types.Message, data: dict):
        if not message.photo:
            return

        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        if throttled.exceeded_count <= 2:
            await message.reply(
                f'Запрос на обработку фотографии можно отправить один раз в {self.rate_limit} секунд.\n'
                'Пожалуйста, подождите.'
            )


class InjectMiddleware(BaseMiddleware):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__()

    async def on_pre_process_message(self, message: Message, data: dict):
        data.update(self.kwargs)

    async def on_pre_process_callback_query(self, callback_query: CallbackQuery, data: dict):
        data.update(self.kwargs)
