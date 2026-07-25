import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

# Токен аз қисми Environment Variables-и Render гирифта мешавад
TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply(
        "Салом! Ин боти табдили видео ба MP3 аст.\n"
        "Лутфан линки видеоро аз YouTube, TikTok ё Instagram фиристед:"
    )

@dp.message()
async def download_audio(message: types.Message):
    url = message.text
    if not url.startswith("http"):
        await message.reply("Лутфан линки дуруст фиристед!")
        return

    processing_msg = await message.reply("⏳ Видео боргирӣ ва ба мусиқӣ табдил дода шуда истодааст, лутфан каме интизор шавед...")

    output_template = f"%(id)s.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
    }

    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                return base + ".mp3"

        mp3_file = await asyncio.to_thread(extract)

        # Файли аудиоро ба истифодабаранда мефиристем
        audio = FSInputFile(mp3_file)
        await message.reply_audio(audio=audio, caption="Марҳамат, мусиқии шумо!")
        
        # Тоза кардани файл аз сервер
        os.remove(mp3_file)
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)

    except Exception as e:
        logging.error(f"Хатогӣ: {e}")
        await message.reply("❌ Мутассифона, зеркашии ин линк муяссар нашуд ё формати он дастгирӣ намешавад.")
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())