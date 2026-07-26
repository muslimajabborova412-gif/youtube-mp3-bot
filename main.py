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

user_links = {}

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
        "👋 Салом!\n"
        "Ин боти зеркашии видео ва мусиқӣ аст.\n\n"
        "👨‍💻 **Таҳиягар:** Шералиев Абдураҳим\n\n"
        "Лутфан линки видеоро аз YouTube, TikTok ё Instagram фиристед:"
    )

@dp.message()
async def get_link(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Лутфан линки дурусти видеоро фиристед!")
        return

    user_links[message.from_user.id] = url

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Видео (MP4)", callback_data="dl_video"),
            InlineKeyboardButton(text="🎵 Мусиқӣ (MP3)", callback_data="dl_mp3")
        ]
    ])

    await message.reply(
        "📥 **Формати дилхоҳро интихоб кунед:**\n\n"
        "👇 Тугмаи зеринро пахш кунед:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("dl_"))
async def process_download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_links:
        await callback.message.answer("❌ Линки видео ёфт нашуд. Лутфан линкро аз нав фиристед.")
        return

    url = user_links[user_id]
    action = callback.data
    
    processing_msg = await callback.message.edit_text("⏳ Боргирӣ оғоз шуд: 0%")

    loop = asyncio.get_event_loop()

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            try:
                coro = bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=processing_msg.message_id,
                    text=f"⏳ Видео боргирӣ шуда истодааст: {percent}"
                )
                asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:
                pass

    ydl_opts = {
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        'progress_hooks': [progress_hook],
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    if action == "dl_mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(id)s.%(ext)s'
        })
    else:
        ydl_opts.update({
            'format': 'best[ext=mp4]/best',
            'outtmpl': '%(id)s.%(ext)s'
        })

    try:
        def download_file():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if action == "dl_mp3":
                    base, _ = os.path.splitext(filename)
                    return base + ".mp3"
                return filename

        file_path = await asyncio.to_thread(download_file)

        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=processing_msg.message_id,
            text="📤 Файл фиристода истодааст..."
        )

        file = FSInputFile(file_path)
        if action == "dl_mp3":
            await bot.send_audio(chat_id=callback.message.chat.id, audio=file, caption="🎧 Мусиқии шумо!\nСозанда: Шералиев Абдураҳим")
        else:
            await bot.send_video(chat_id=callback.message.chat.id, video=file, caption="🎬 Видеои шумо!\nСозанда: Шералиев Абдураҳим")

        os.remove(file_path)
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        logging.error(f"Хатогӣ: {e}")
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=processing_msg.message_id,
            text="❌ Мутассифона, зеркашии ин линк муяссар нашуд."
        )

    await callback.answer()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
