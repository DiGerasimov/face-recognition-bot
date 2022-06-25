import asyncio
import logging
import multiprocessing
from io import BytesIO
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, ContentType, MediaGroup, InputFile
from aiogram.utils import executor
from dialog.telegram import Dialog
from dotenv import load_dotenv

from middlewares import InjectMiddleware, ThrottlingMiddleware
from recognition import load_image_from_bytes, find_clones
from utils import increase_number_in_search, decrease_number_in_search, get_number_in_search


load_dotenv()

MAX_SUB_PROCESSES = int(getenv('MAX_SUB_PROCESSES', 1))

logging.basicConfig(level=logging.INFO)

bot = Bot(getenv('TOKEN'), parse_mode='HTML')
dp = Dispatcher(bot=bot, storage=MemoryStorage())

semaphore = multiprocessing.Semaphore(MAX_SUB_PROCESSES)


def send_founded_photos(message_as_dict: dict):
    Bot.set_current(bot)

    message = Message(**message_as_dict)

    loop = asyncio.get_event_loop()
    run = loop.run_until_complete

    photo: BytesIO = run(message.photo[-1].download(destination=BytesIO()))

    photos = []
    messages_sent = 0

    with semaphore:
        run(message.reply(
            'Обработка вашей фотографии началась!'
        ))

        for clone in find_clones(load_image_from_bytes(photo), tolerance=0.5):
            with open(clone, 'rb') as f:
                photos.append(BytesIO(f.read()))

            if len(photos) == 10:
                media = MediaGroup()

                for photo in photos:
                    media.attach_photo(InputFile(photo))

                run(message.reply_media_group(media))

                photos = []

                messages_sent += 1

        if not photos and not messages_sent:
            run(message.reply('К сожалению, фото с вами не были найдены :('))
        elif not messages_sent:
            if len(photos) == 1:
                run(message.answer_photo(photos[0]))
            else:
                media = MediaGroup()

                for photo in photos:
                    media.attach_photo(InputFile(photo))

                run(message.reply_media_group(media))


@dp.message_handler(commands='start')
async def send_hello_message(message: Message):
    await message.answer(
        'Привет!\n'
        'Отправь мне своё селфи и я попробую найти тебя!'
    )


@dp.message_handler(content_types=ContentType.PHOTO)
async def send_client_photos(message: Message, pool):
    increase_number_in_search()

    if get_number_in_search() > MAX_SUB_PROCESSES:
        await message.reply(
            'Обработка вашей фотографии скоро начнется!\n'
            f'Место в очереди: {get_number_in_search() - MAX_SUB_PROCESSES}'
        )

    pool.apply_async(
        send_founded_photos,
        args=(dict(message), ),
        callback=decrease_number_in_search,
        error_callback=lambda exc: print(exc)
    )


def run_bot():
    dp.setup_middleware(ThrottlingMiddleware(10))
    dp.setup_middleware(InjectMiddleware(pool=multiprocessing.Pool(MAX_SUB_PROCESSES)))

    Dialog.register_handlers(dp)

    executor.start_polling(dp)


if __name__ == '__main__':
    run_bot()
