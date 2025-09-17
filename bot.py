# filename: tg_virtual_girlfriend.py
import os
import json
import tempfile
import requests
from io import BytesIO
from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")   # ✅ token desde Railway
IMAGE_API_URL = os.getenv("IMAGE_API_URL", "https://api.example-image.service/generate")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY", "")
VOICE_PROVIDER = "gtts"

DATA_FILE = "profiles.json"

# --- UTIL: profiles store ---
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_profiles():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_profiles(profiles):
    with open(DATA_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def get_or_create_profile(chat_id):
    profiles = load_profiles()
    if str(chat_id) not in profiles:
        profiles[str(chat_id)] = {
            "name": "Lucía",
            "age_appearance": "22-28",
            "ethnicity": "latina-europea",
            "body": "atlética, cuerpo brasileño",
            "attitude": "pícara",
            "seed": 123456,
            "last_prompt": ""
        }
        save_profiles(profiles)
    return profiles[str(chat_id)]

def update_profile(chat_id, newdata):
    profiles = load_profiles()
    profiles[str(chat_id)].update(newdata)
    save_profiles(profiles)

# --- IMAGE GENERATION (placeholder) ---
def generate_image(prompt, seed=None):
    payload = {"prompt": prompt, "seed": seed, "width":512, "height":768}
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}"}
    r = requests.post(IMAGE_API_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return BytesIO(r.content)

# --- TTS ---
def text_to_speech(text, lang="es"):
    tts = gTTS(text, lang=lang)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = get_or_create_profile(update.effective_chat.id)
    text = (f"Hola — soy tu novia virtual *{profile['name']}*.\n"
            f"Usa /foto /audio /video /perfil /set para personalizarme.")
    kb = [[InlineKeyboardButton("Ver perfil", callback_data="ver_perfil")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def perfil_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = get_or_create_profile(update.effective_chat.id)
    txt = "\n".join(f"{k}: {v}" for k, v in profile.items())
    await update.message.reply_text(txt)

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /set <campo> <valor>")
        return
    field = args[0]
    value = " ".join(args[1:])
    update_profile(update.effective_chat.id, {field: value})
    await update.message.reply_text(f"{field} actualizado a: {value}")

async def foto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = get_or_create_profile(update.effective_chat.id)
    prompt = (
        f"A realistic selfie of a young spanish woman with mixed {profile['ethnicity']} features, "
        f"{profile['body']}, playful (pícara) expression, warm tan skin, shoulder-length dark hair, "
        "casual urban clothes, soft golden-hour lighting, photorealistic, high detail"
    )
    profile['last_prompt'] = prompt
    update_profile(update.effective_chat.id, {"last_prompt": prompt})

    await update.message.reply_text("Generando foto... ⏳")
    try:
        img_bytes = generate_image(prompt, seed=profile.get("seed"))
    except Exception as e:
        await update.message.reply_text("Error generando imagen: " + str(e))
        return

    img_bytes.seek(0)
    await update.message.reply_photo(photo=img_bytes, caption=f"{profile['name']} — foto")

async def audio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    profile = get_or_create_profile(update.effective_chat.id)
    text = " ".join(context.args) if context.args else f"Hola cariño, soy {profile['name']}. ¿Qué quieres hacer hoy?"
    text = f"{text} (voz suave y pícara, acento español)"
    mp3_path = text_to_speech(text)
    with open(mp3_path, "rb") as f:
        await update.message.reply_audio(f, caption=f"Audio de {profile['name']}")
    os.remove(mp3_path)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ver_perfil":
        profile = get_or_create_profile(update.effective_chat.id)
        txt = "\n".join(f"{k}: {v}" for k, v in profile.items())
        await query.edit_message_text(txt)

# --- Main ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("perfil", perfil_cmd))
    app.add_handler(CommandHandler("set", set_cmd))
    app.add_handler(CommandHandler("foto", foto_cmd))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("✅ Bot running...")
    app.run
