import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply(
        "Салом! Ин боти табдили видео ба MP3 аст.\n"
        "Лутфан линки видеоро аз YouTube, TikTok ё Instagram фиристед:\n\n"
        "Бо фармони /info метавонед маълумоти бештар гиред."
    )

@dp.message(Command("info"))
async def send_info(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Тарзи истифода", callback_data="how_to_use")],
        [InlineKeyboardButton(text="🌐 Шабакаҳои дастгиришаванда", callback_data="platforms")]
    ])
    await message.reply(
        "ℹ️ **Маълумот дар бораи бот:**\n\n"
        "Ин бот видеоҳоро аз YouTube, TikTok ва Instagram ба мусиқии MP3 табдил медиҳад.\n"
        "Танҳо линки видеоро равон кунед ва мусиқии худро қабул кунед!",
        reply_markup=keyboard
    )

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "how_to_use":
        await callback.message.answer("1. Линки видеоро аз Ютуб, Инстаграм ё ТикТок нусхабардорӣ кунед.\n2. Онро ба ҳамин чат фиристед.\n3. Чанд сония интизор шавед ва файли MP3-ро зеркашӣ кунед!")
    elif callback.data == "platforms":
        await callback.message.answer("Мо ин платформаҳоро дастгирӣ мекунем:\n- YouTube\n- TikTok\n- Instagram")
    await callback.answer()

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
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
    }

    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                return base + ".mp3"

        mp3_file = await asyncio.to_thread(extract)

        audio = FSInputFile(mp3_file)
        await message.reply_audio(audio=audio, caption="Марҳамат, мусиқии шумо!")
        
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
