import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pydub import AudioSegment
import speech_recognition as sr

# Конфигурация
TOKEN = "input API here"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB максимальный размер файла
SUPPORTED_LANGUAGES = {'ru': 'ru-RU', 'en': 'en-US'}

# Инициализация распознавателя
recognizer = sr.Recognizer()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправьте мне голосовое сообщение или аудиофайл, и я преобразую его в текст.\n"
        "Поддерживаемые языки: русский, английский"
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем файл
        if update.message.voice:
            file = await update.message.voice.get_file()
            ext = "ogg"
        elif update.message.audio:
            file = await update.message.audio.get_file()
            ext = os.path.splitext(file.file_path)[1][1:]
        else:
            await update.message.reply_text("Пожалуйста, отправьте аудиофайл или голосовое сообщение")
            return

        # Проверка размера файла
        if file.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("Файл слишком большой. Максимальный размер 20MB")
            return

        # Скачивание файла
        input_file = f"temp_{update.update_id}.{ext}"
        await file.download_to_drive(input_file)

        # Конвертация в WAV
        audio = AudioSegment.from_file(input_file)
        wav_file = f"temp_{update.update_id}.wav"
        audio.export(wav_file, format="wav")

        # Распознавание речи
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
            
            # Автодетект языка
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
            except:
                text = recognizer.recognize_google(audio_data, language="en-US")

        await update.message.reply_text(f"Распознанный текст:\n\n{text}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка обработки аудио: {str(e)}")
    finally:
        # Удаление временных файлов
        if 'input_file' in locals() and os.path.exists(input_file):
            os.remove(input_file)
        if 'wav_file' in locals() and os.path.exists(wav_file):
            os.remove(wav_file)

def main():
    # Создаем приложение и передаем токен
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Регистрируем обработчики сообщений
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))

    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
