import os
from telegram.ext import Application, CommandHandler

# Lee el token desde las Variables de Railway
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Crea la aplicación del bot
app = Application.builder().token(TOKEN).build()

# Comando /start
async def start(update, context):
    await update.message.reply_text("¡Hola! Tu bot ya está corriendo en Railway 🚀")

# Registrar comandos
app.add_handler(CommandHandler("start", start))

print("✅ Bot corriendo... (esperando mensajes en Telegram)")
app.run_polling()
