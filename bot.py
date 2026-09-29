import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from vkbottle.bot import Bot, Message

load_dotenv()

VK_GROUP_TOKEN = os.environ["VK_GROUP_TOKEN"]
AI_API_KEY = os.environ["AI_API_KEY"]
AI_BASE_URL = os.environ["AI_BASE_URL"]
AI_MODEL = os.environ["AI_MODEL"]
BOT_SYSTEM_PROMPT = os.environ["BOT_SYSTEM_PROMPT"]

START_ANSWER = "Привет! Я AI-бот сообщества. Напишите вопрос — постараюсь помочь."
AI_ERROR_ANSWER = "Сейчас не могу получить ответ от AI. Попробуйте немного позже."

bot = Bot(token=VK_GROUP_TOKEN)
ai_client = AsyncOpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)


async def ask_ai(prompt: str) -> str:
    completion = await ai_client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": BOT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return (completion.choices[0].message.content or "").strip()


@bot.on.message(from_user=True)
async def handle_message(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    command = text.split()[0].lower()
    if command == "/start" or command.startswith("/start@"):
        await message.answer(START_ANSWER)
        return

    try:
        answer = await ask_ai(text)
    except Exception:
        await message.answer(AI_ERROR_ANSWER)
        return

    await message.answer(answer or AI_ERROR_ANSWER)


async def main() -> None:
    await bot.run_polling()


asyncio.run(main())
