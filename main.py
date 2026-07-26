import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

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
        "Ин боти зеркашии видео аз YouTube ва Instagram аст.\n\n"
        "👨‍💻 **Таҳиягар:** Шералиев Абдураҳим\n\n"
        "Лутфан линки видеоро фиристед:"
    )

@dp.message()
async def download_media(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Лутфан линки дурусти видеоро фиристед!")
        return

    msg = await message.reply("⏳ Видео боргирӣ шуда истодааст, лутфан интизор шавед...")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'video.mp4',
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        def download():
            if os.path.exists('video.mp4'):
                os.remove('video.mp4')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(download)

        if os.path.exists('video.mp4'):
            await msg.edit_text("📤 Видео ба Телеграм фиристода истодааст...")
            file = FSInputFile('video.mp4')
            await message.reply_video(video=file, caption="🎬 Видеои шумо!\nСозанда: Шералиев Абдураҳим")
            await msg.delete()
            os.remove('video.mp4')
        else:
            await msg.edit_text("❌ Мутассифона, видео ёфт нашуд ё зеркашӣ نشд.")

    except Exception as e:
        logging.error(f"Хатогӣ: {e}")
        await msg.edit_text("❌ Хатогӣ рӯй дод. Эҳтимол видео калон аст ё линк нодуруст аст.")

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
