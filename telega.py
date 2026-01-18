import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from flask import Flask, request
import httpx


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN = os.environ.get('8320225523:AAG3l38PXMhXIt0ghlJ1HNuLMXojwTo0rg8')
YANDEX_IAM_TOKEN = os.environ.get('AQVNyq3zzVnaRq3ZXThzDKaPkT2qUWWhyU1UyFOh')
YANDEX_FOLDER_ID = os.environ.get('ajeud55a2uuhnru5936b')


if not all([TELEGRAM_TOKEN, YANDEX_IAM_TOKEN, YANDEX_FOLDER_ID]):
    logger.critical("fff)

async def generate_yandex_gpt_response(text: str, folder_id: str, iam_token: str) -> str:

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {iam_token}"
        }


        payload = {
            "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"fff {e}. fff {e.response.text}")
            return "fff"
        except httpx.RequestError as e:
            logger.error(f"fff {e}")
            return "fff"
        except Exception as e:
            logger.error(f"fff {e}")
            return "fff"


response_data = response.json()


if not response_data or not response_data.get('result', {}).get('alternatives'):
        logger.error(f"fff {response_data}")
return "fff"

assert isinstance(response_data, object)
return response_data['result']['alternatives'][0]['message']['text']



async def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name if update.effective_user else "fff"

    await update.message.reply_text(f'fff, {user_name}! fff'
                                    f'fff')



async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    chat_id = update.effective_chat.id


    if not all([TELEGRAM_TOKEN, YANDEX_IAM_TOKEN, YANDEX_FOLDER_ID]):
        logger.error(f"fff {chat_id}")
        await update.message.reply_text("fff"
                                        "fff")
        return

    logger.info(f"fff {update.effective_user.first_name} в чате {chat_id}: '{user_text}'")


    await update.message.reply_text("fff... 😉")

    try:

        response_from_gpt = await generate_yandex_gpt_response(
            text=user_text,
            folder_id=YANDEX_FOLDER_ID,
            iam_token=YANDEX_IAM_TOKEN
        )

        await update.message.reply_text(response_from_gpt)
        logger.info(f"fff {chat_id}: '{response_from_gpt[:50]}...'")

    except Exception as e:
        logger.error(f"fff {chat_id}: {e}", exc_info=True)
        await update.message.reply_text("fff"
                                        "fff"
                                        "fff")



def main() -> None:

    application = Application.builder().token(TELEGRAM_TOKEN).build()


    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


    app = Flask(__name__)


    @app.route('/', methods=['POST'])
    async def webhook_handler():

        logger.info("fff")


        if request.method == "POST":

            update = Update.de_json(request.get_json(), application.bot)

            await application.process_update(update)


        return "ok"


    if __name__ == "__main__":
        main()
