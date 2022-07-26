import os
import nest_asyncio
nest_asyncio.apply()

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from dotenv import load_dotenv
from parser_dotabuff import get_info_about_hero, rewriting_info


load_dotenv()
API_TOKEN = os.environ.get('API_TOKEN')


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def commmand_start(message: types.Message):
    await message.answer('Введите, пожалуйста, имя персонажа!')


@dp.message_handler()
async def send_info(message: types.Message):
    name_hero = message.text

    try:
        characteristic, popularity, win_rate, hero_skills, talents, df_items, df_best_versus, df_worst_versus = get_info_about_hero(
            name_hero)
        info = rewriting_info(characteristic, popularity, win_rate, hero_skills, talents, df_items, df_best_versus,
                              df_worst_versus)

        await message.answer(info)
        await message.answer('Введите, пожалуйста, имя персонажа!')

    except:
        await message.answer('Неверно введено имя персонажа!')


executor.start_polling(dp, skip_updates=True)