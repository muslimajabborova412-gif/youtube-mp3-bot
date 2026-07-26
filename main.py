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

# Барои дар хотир доштани линки фиристодаи корбар
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

    # Линкро захира мекунем барои ҳамин корбар
    user_links[message.from_user.id] = url

    # Кнопкаҳои интихоби сифат монанди расми фиристодаатон
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ 144p", callback_data="dl_144"),
            InlineKeyboardButton(text="⚡ 360p", callback_data="dl_360")
        ],
        [
            InlineKeyboardButton(text="⚡ 480p", callback_data="dl_480"),
            InlineKeyboardButton(text="⚡ 720p", callback_data="dl_720")
        ],
        [
            InlineKeyboardButton(text="⚡ 1080p", callback_data="dl_1080"),
            InlineKeyboardButton(text="🎵 MP3", callback_data="dl_mp3")
        ]
    ])

    await message.reply(
        "📥 **Формат ва сифати дилхоҳро интихоб кунед:**\n\n"
        "👇 Тугмаҳои зеринро пахш кунед:",
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
    await callback.message.edit_text("⏳ Боргирӣ оғоз шуд, лутфан интизор шавед...")

    ydl_opts = {
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
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
    elif action == "dl_144":
        ydl_opts.update({'format': 'bestvideo[height<=144]+bestaudio/best[height<=144]', 'outtmpl': '%(id)s.%(ext)s'})
    elif action == "dl_360":
        ydl_opts.update({'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]', 'outtmpl': '%(id)s.%(ext)s'})
    elif action == "dl_480":
        ydl_opts.update({'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]', 'outtmpl': '%(id)s.%(ext)s'})
    elif action == "dl_720":
        ydl_opts.update({'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]', 'outtmpl': '%(id)s.%(ext)s'})
    elif action == "dl_1080":
        ydl_opts.update({'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]', 'outtmpl': '%(id)s.%(ext)s'})

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

        await callback.message.edit_text("📤 Файл фиристода истодааст...")

        file = FSInputFile(file_path)
        if action == "dl_mp3":
            await bot.send_audio(chat_id=callback.message.chat.id, audio=file, caption="🎧 Мусиқии шумо!\nСозанда: Шералиев Абдураҳим")
        else:
            await bot.send_video(chat_id=callback.message.chat.id, video=file, caption="🎬 Видеои шумо!\nСозанда: Шералиев Абдураҳим")

        os.remove(file_path)
    except Exception as e:
        logging.error(f"Хатогӣ: {e}")
        await callback.message.edit_text("❌ Мутассифона, зеркашии ин сифат муяссар нашуд ё видео ин қадар сифат надорад.")

    await callback.answer()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
