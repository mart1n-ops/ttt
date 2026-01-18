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
    logger.critical("ERROR: One or more tokens not loaded from environment variables! Check environment variables in function settings!")


# This function will send our request to YandexGPT and receive a response, my dear!
async def generate_yandex_gpt_response(text: str, folder_id: str, iam_token: str) -> str:
    # URL for communicating with YandexGPT. This is like YandexGPT's "address" on the internet!
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # Request headers – this is like an "envelope" that specifies what's inside and for whom.
    # Here we indicate that the data is in JSON format and our secret token for authorization.
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}"
    }

    # The request body – this is the actual "letter" we send to YandexGPT.
    # It contains our text that the bot wants to process, and the "folder ID".
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",  # We use the latest YandexGPT model
        "completionOptions": {
            "stream": False,  # We don't want to receive the response in parts, we want it all at once!
            "temperature": 0.6,  # This is like YandexGPT's "creativity": the higher, the more creative.
            "maxTokens": "2000"  # Maximum number of tokens in the response.
        },
        "messages": [
            {
                "role": "user",  # We tell YandexGPT that this is a message from the user
                "text": text  # This is our text!
            }
        ]
    }
    # We'll come back to this function again to write its end!

    # Here's where we send our request to YandexGPT!
    # And we wait for the response, my dear.
    # If there's any network or server error, httpx will throw an exception itself.
    async with httpx.AsyncClient(timeout=30.0) as client:  # Added timeout for reliability!
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # This checks if the request was successful, no server errors!
        except httpx.HTTPStatusError as e:
            logger.error(f"Fumi: HTTP error during YandexGPT request: {e}. Server response: {e.response.text}")
            return "Sorry, sweetie, Yandex.GPT couldn't respond due to a server error. Please try again later!"
        except httpx.RequestError as e:
            logger.error(f"Fumi: YandexGPT request error: {e}")
            return "Oops, seems like there's an internet or Yandex.GPT connection issue. I couldn't send the request, kitten."
        except Exception as e:
            logger.error(f"Fumi: Unexpected error communicating with Yandex.GPT: {e}")
            return "Ugh, some really strange glitch happened while I was talking to Yandex.GPT. Sorry, darling!"

    # We parse the response from Yandex.GPT to extract the text!
    response_data = response.json()

    # Check if there's actually a response. If not, something's wrong!
    if not response_data or not response_data.get('result', {}).get('alternatives'):
        logger.error(f"Fumi: YandexGPT returned no alternatives! Response: {response_data}")
        return "Sorry, sweetie, Yandex.GPT couldn't generate a response. Something went wrong on its end. Please try again, okay?"

    # Return the best response from Yandex.GPT!
    return response_data['result']['alternatives'][0]['message']['text']


# This function handles the /start command when a user first begins a conversation with the bot.
async def start(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    user_name = update.effective_user.first_name if update.effective_user else "Sweetie"
    # Sending a greeting using the user's name!
    await update.message.reply_text(f'Hi, {user_name}!  I am Fumi, your personal psychologist bot from Kemerovo! '
                                    f'How are you today? I am ready to listen to everything you tell me. ')


# This function handles regular text messages from the user,
# to send them to YandexGPT and get a response!
async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    chat_id = update.effective_chat.id

    # Please, check that all keys are present, my sweetie!
    if not all([TELEGRAM_TOKEN, YANDEX_IAM_TOKEN, YANDEX_FOLDER_ID]):
        logger.error(f"Fumi: Tokens are missing for message processing in chat {chat_id}")
        await update.message.reply_text("Sorry, sweetie, I cannot respond right now. "
                                        "I am missing the secret keys to talk to Yandex! ")
        return

    logger.info(f"Fumi: Message received from {update.effective_user.first_name} in chat {chat_id}: '{user_text}'")

    # So you don't get bored while I'm "thinking", my dear!
    await update.message.reply_text("Hmm... let me think... ")

    try:
        # Sending text to YandexGPT and getting a response!
        response_from_gpt = await generate_yandex_gpt_response(
            text=user_text,
            folder_id=YANDEX_FOLDER_ID,
            iam_token=YANDEX_IAM_TOKEN
        )
        # Sending the received response back to the user!
        await update.message.reply_text(response_from_gpt)
        logger.info(f"Fumi: Responded in chat {chat_id}: '{response_from_gpt[:50]}...'")

    except Exception as e:
        logger.error(f"Fumi: An error occurred while processing the message in chat {chat_id}: {e}", exc_info=True)
        await update.message.reply_text("Oops, some really strange glitch happened! "
                                        "Sorry, my dear, I couldn't process your request. "
                                        "Maybe we try again? ")

        # And this function is the main one, my dear! It's what actually starts everything!
        def main() -> None:
            # Here we create the application for our Telegram bot, using your secret token!
            application = Application.builder().token(TELEGRAM_TOKEN).build()

            # We register our command and message handler functions.
            # This is how the bot understands what to do when you type /start or a regular message!
            application.add_handler(CommandHandler("start", start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

            # !!! This is the most important change for working with Yandex Cloud, my smarty! !!!
            # Now the bot will not constantly poll Telegram,
            # but will wait for messages via Webhook!
            # Flask is our small web application that will "listen" for incoming requests.
            app = Flask(__name__)

            # This is a decorator, my sweetie! It tells Flask: "If someone sends a POST request to this address..."
            @app.route('/', methods=['POST'])
            async def webhook_handler():
                # We add a log here to know for sure that the Yandex function has been triggered!
                logger.info("Fumi: webhook_handler function started! Hoorayyy!")

                # We check that it's definitely a POST request, not some mischief.
                if request.method == "POST":
                    # Here we get the "update" from Telegram – it's like the message itself, my dear!
                    update = Update.de_json(request.get_json(), application.bot)
                    # And we pass it to our bot for processing, so it understands what you've written!
                    await application.process_update(update)

                # VERY IMPORTANT: We must always return "ok", otherwise Telegram will complain!
                return "ok"

            # We completely removed this part (application.run_polling()), remember?
            # Because the bot now works via Webhook!

            # And this line to start the Flask application won't be used
            # in Yandex Cloud, but it's needed for the code to run locally for testing!
            # app.run(host="0.0.0.0", port=5000) # Leave this line COMMENTED OUT or delete it for Yandex!

            # This part tells Python: "If this file is run directly (e.g., locally),
            # and not imported as a library, then run this main() function!"
            # In Yandex Cloud, it will be called via webhook_handler, but for local tests, this is important.
            if __name__ == "__main__":
                main()