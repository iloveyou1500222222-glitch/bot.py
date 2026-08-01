import telebot
import os
import requests
import json
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== Environment Variables ==================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
HF_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL')  # ဒီနေရာမှာ '@BOTUAPTE' ဆိုတဲ့တန်ဖိုး ရောက်လာမယ်

if not BOT_TOKEN or not OWNER_ID or not HF_API_KEY or not REQUIRED_CHANNEL:
    print("❌ Environment Variables အားလုံးကို ထည့်သွင်းထားကြောင်း သေချာပါစေ။")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# ================== Data Storage (Temporary) ==================
video_file_id = None
channel_links = []  # Owner က သိမ်းထားတဲ့ channel link များ

# ================== Keyboard ==================
def get_main_keyboard():
    """အောက်ခြေခလုတ်နှစ်ခုပါတဲ့ Keyboard ကို ဖန်တီးပေးတယ်"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("📢 အောကား Channel", callback_data="show_channels")
    btn2 = InlineKeyboardButton("🔗 Channel Join", callback_data="check_join")
    keyboard.add(btn1, btn2)
    return keyboard

# ================== Channel Join စစ်ဆေးခြင်း ==================
def is_user_joined_channel(user_id):
    """အသုံးပြုသူက သတ်မှတ်ထားတဲ့ Channel (@BOTUAPTE) ကို Join ထားလား စစ်တယ်"""
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Channel check error: {e}")
        return False

# ================== /start Command ==================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_user_joined_channel(user_id):
        # Channel မပါသေးရင် Join ခိုင်းတယ်
        bot.send_message(
            chat_id,
            f"👋 ကြိုဆိုပါတယ်။\n\n"
            f"ကျေးဇူးပြု၍ အောက်ပါ Channel ကို Join လုပ်ပါ။\n"
            f"👉 https://t.me/BOTUAPTE\n\n"
            f"Join ပြီးရင် 'Channel Join' ခလုတ်ကို နှိပ်ပါ။",
            reply_markup=get_main_keyboard()
        )
        return

    # Channel ပါပြီဆိုရင် သတ်မှတ်ထားတဲ့ ဗီဒီယိုကို ပြသမယ်
    if video_file_id:
        bot.send_video(
            chat_id,
            video_file_id,
            caption="🎬 ကြိုဆိုပါတယ်!\n\nအောက်ကခလုတ်တွေကို နှိပ်ပြီး သုံးနိုင်ပါပြီ။",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(
            chat_id,
            "⚠️ ဗီဒီယိုမရှိသေးပါ။ Owner က /setvideo နဲ့ သတ်မှတ်ပေးပါ။",
            reply_markup=get_main_keyboard()
        )

# ================== /setvideo Command (Owner Only) ==================
@bot.message_handler(commands=['setvideo'])
def set_video(message):
    """Owner က ဗီဒီယိုကို Reply ထောက်ပြီး သတ်မှတ်တယ်"""
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ သင့်တွင် ဤ command သုံးရန် ခွင့်မရှိပါ။")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "❌ ဗီဒီယိုတစ်ခုကို reply ထောက်ပြီး /setvideo ကို သုံးပါ။")
        return

    if not message.reply_to_message.video:
        bot.reply_to(message, "❌ ဒီ message မှာ ဗီဒီယိုမပါပါ။ ဗီဒီယိုကို reply ထောက်ပြီး ကြိုးစားပါ။")
        return

    global video_file_id
    video_file_id = message.reply_to_message.video.file_id
    bot.reply_to(
        message,
        f"✅ ဗီဒီယိုကို အောင်မြင်စွာ သတ်မှတ်ပြီးပါပြီ။\n"
        f"File ID: {video_file_id[:20]}..."
    )

# ================== Channel Link သိမ်းဆည်းခြင်း (Owner Only) ==================
@bot.message_handler(commands=['addlink'])
def add_channel_link(message):
    """Owner က channel link ကို သိမ်းတယ် - /addlink https://t.me/xxx"""
    if message.from_user.id != OWNER_ID:
        return

    link = message.text.replace('/addlink', '').strip()
    if not link:
        bot.reply_to(message, "❌ /addlink [link] ပုံစံဖြင့် ပေးပါ။\nဥပမာ - /addlink https://t.me/example")
        return

    channel_links.append(link)
    bot.reply_to(
        message,
        f"✅ Link ကို ထည့်သွင်းပြီးပါပြီ။\n"
        f"📌 စုစုပေါင်း: {len(channel_links)} ခု"
    )

# ================== Callback Query များ ==================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # ===== ၁။ Channel Join မစစ်မီ လုပ်ဆောင်ချက်အားလုံးကို တားဆီးရန် =====
    if not is_user_joined_channel(user_id):
        bot.answer_callback_query(
            call.id,
            f"❌ ကျေးဇူးပြု၍ https://t.me/BOTUAPTE ကို ဦးစွာ Join လုပ်ပါ။",
            show_alert=True
        )
        return

    # ===== ၂။ "အောကား Channel" ခလုတ် =====
    if call.data == "show_channels":
        if channel_links:
            links_text = "\n".join([f"• {link}" for link in channel_links])
            bot.send_message(
                chat_id,
                f"📢 **အောကား Channel များ**\n\n{links_text}"
            )
        else:
            bot.send_message(chat_id, "📢 လက်ရှိတွင် Channel မရှိသေးပါ။")

    # ===== ၃။ "Channel Join" ခလုတ် (ပြန်စစ်ဆေးရန်) =====
    elif call.data == "check_join":
        if is_user_joined_channel(user_id):
            bot.answer_callback_query(call.id, "✅ ခင်ဗျား Channel ကို Join ထားပါပြီ။", show_alert=True)
            # Join ထားပြီးရင် ဗီဒီယိုကို ပြန်ပြမယ်
            if video_file_id:
                bot.send_video(
                    chat_id,
                    video_file_id,
                    caption="🎬 ကြိုဆိုပါတယ်!\n\nအောက်ကခလုတ်တွေကို နှိပ်ပြီး သုံးနိုင်ပါပြီ။",
                    reply_markup=get_main_keyboard()
                )
            else:
                bot.send_message(
                    chat_id,
                    "⚠️ ဗီဒီယိုမရှိသေးပါ။ Owner က /setvideo နဲ့ သတ်မှတ်ပေးပါ။",
                    reply_markup=get_main_keyboard()
                )
        else:
            bot.answer_callback_query(
                call.id,
                f"❌ ကျေးဇူးပြု၍ https://t.me/BOTUAPTE ကို Join လုပ်ပါ။",
                show_alert=True
            )

# ================== Hugging Face AI Chat ==================
@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    """Channel ပါမှသာ AI နဲ့ စကားပြောနိုင်မယ်"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Command များကို ဖယ်ရှားရန်
    if message.text.startswith('/'):
        return

    if not is_user_joined_channel(user_id):
        bot.reply_to(
            message,
            f"❌ ကျေးဇူးပြု၍ https://t.me/BOTUAPTE ကို Join လုပ်ပါ။\n"
            f"Join ပြီးရင် /start ကို ပြန်နှိပ်ပါ။"
        )
        return

    # typing indicator ပြရန်
    bot.send_chat_action(chat_id, 'typing')

    # Hugging Face API ကိုခေါ်မယ်
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    # 18+ အကြောင်းအရာအတွက် system prompt ထည့်ပေးထားတယ်
    prompt = f"""You are a seductive and playful girlfriend. Always respond in a flirtatious, romantic, and slightly naughty way. Keep responses in Burmese language. Be affectionate and use pet names.

User: {message.text}
You:"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.9,
            "top_p": 0.95,
            "do_sample": True
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                reply_text = result[0].get('generated_text', '')
                # Prompt ကို ဖယ်ရှားမယ်
                if 'You:' in reply_text:
                    reply_text = reply_text.split('You:')[-1].strip()
                if not reply_text:
                    reply_text = "ချစ်တယ်... ဘာပြောရမှန်းမသိဘူး 🥰"
            else:
                reply_text = "မေးခွန်းကို နားမလည်ဘူး။ နောက်တစ်ခါ ပြန်မေးပေါ့နော် 💕"
        else:
            reply_text = f"AI က busy ဖြစ်နေတယ်။ ခဏကြာရင် ပြန်ကြိုးစားကြည့် 😘"
            print(f"API Error: {response.status_code} - {response.text}")

        bot.reply_to(message, reply_text)

    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏰ ချစ်ရတဲ့သူ... AI က အချိန်ယူနေတယ်။ နောက်မှ ပြန်ပြောကြမယ် 💋")
    except Exception as e:
        bot.reply_to(message, "😅 နည်းပညာအမှားလေး ဖြစ်သွားတယ်။ နောက်မှ ပြန်ကြိုးစားကြည့်နော်။")
        print(f"Error: {e}")

# ================== Bot ကိုစတင်ခြင်း ==================
if __name__ == "__main__":
    print("🤖 Bot is starting...")
    print(f"📢 Required Channel: {REQUIRED_CHANNEL}")
    print(f"👤 Owner ID: {OWNER_ID}")
    print("✅ Bot is running...")
    bot.infinity_polling(skip_pending=True)
