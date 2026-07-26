import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Веб-сервери хурд барои порти Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

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

    processing_msg = await message.reply("⏳ Боргирӣ оғоз шуд: 0%")

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            try:
                coro = bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=processing_msg.message_id,
                    text=f"⏳ Видео боргирӣ шуда истодааст: {percent}"
                )
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:
                pass

    loop = asyncio.get_event_loop()

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
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',  # Номи файли куки дар GitHub бояд айнан cookies.txt бошад
        'progress_hooks': [progress_hook],
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                return base + ".mp3"

        mp3_file = await asyncio.to_thread(extract)

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text="🎵 Ба мусиқӣ табдил дода шуд, фиристода истодааст..."
        )

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
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
