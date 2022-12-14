from aiogram import types
from aiogram.types import ContentType
from tg.utils import States
from tg.messages import MESSAGES, BUILDINGS_DICT
from tg.keyboards import *
import datetime as dt
from tools.tools import delete_outdated_files, save_photo, \
    generate_unique_filename, get_formatted_now_date
from bot_main import submit_logger
from bot_main import dp, bot


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES["start"], reply=False)


@dp.message_handler(commands=['help'])
async def process_help_command(msg: types.Message):
    await bot.send_message(msg.from_user.id, MESSAGES["help"])


@dp.message_handler(content_types=ContentType.PHOTO)
async def process_get_photo_command(msg: types.Message):
    await msg.photo[-1].download("flask_app/static/photos/base_name.jpg")
    state = dp.current_state(user=msg.from_user.id)
    await bot.send_message(msg.from_user.id, MESSAGES["ask_building"],
                           reply_markup=choose_building_markup)
    await state.set_state(States.all()[0])


@dp.message_handler(state=States.STATE1_GET_BUILDING)
async def get_building(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text not in BUILDINGS_DICT.keys():
        await bot.send_message(msg.from_user.id, MESSAGES["building_error"],
                               reply_markup=choose_building_markup)
        await state.set_state(States.all()[0])
    else:
        await state.update_data(building=BUILDINGS_DICT[msg.text])
        await bot.send_message(msg.from_user.id, MESSAGES["ask_room"])
        await state.set_state(States.all()[1])


@dp.message_handler(state=States.STATE2_GET_ROOM)
async def get_room(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    state_data = await state.get_data()
    try:
        room_number = int(msg.text)
        if not 100 <= room_number <= 999:
            raise ValueError
    except ValueError:
        await bot.send_message(msg.from_user.id, MESSAGES["room_error"])
        await state.set_state(States.all()[1])
    else:
        building = state_data["building"]
        date = get_formatted_now_date()
        delete_outdated_files(building)
        filename = generate_unique_filename(date, room_number)
        save_photo(building, filename)
        submit_logger.update(msg, str(dt.datetime.now()), room_number,
                             f"{building}/{filename}")
        await bot.send_message(msg.from_user.id, MESSAGES["finish"])
        await state.finish()
