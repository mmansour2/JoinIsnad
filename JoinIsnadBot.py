import datetime
import logging
import re
import time
from typing import List, Optional, Tuple
from logging.handlers import RotatingFileHandler
import telegram
from fastapi import BackgroundTasks, FastAPI, HTTPException
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          Filters, MessageHandler, Updater, filters)
import logging
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from typing import List
import telegram
from fastapi import (BackgroundTasks, Depends, FastAPI, File, Header,
                     HTTPException, Path, Query, UploadFile)
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          Filters, MessageHandler, Updater, filters)

# configure the log format
formatter  = logging.Formatter('%(asctime)s - %(message)s')

handler = RotatingFileHandler('app.log', maxBytes=1024*1024*10, backupCount=5)
handler.setFormatter(formatter)
# set the logging level to INFO
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# add the handler to the logger
logger = logging.getLogger(__name__)
logger.addHandler(handler)


description = """

## Isnad Tasks - Util API <img src=\'https://flagcdn.com/24x18/ps.png\'> 🔻🔻🔻


Isnad tasks - is a powerful tool designed to streamline Isnad tasks.

The following APIs provide various services for managing tasks, handling target user IDs, and reading file contents.

**Key Features:**

- **Reset User:**
    Reset the user if blocked, so he can start new request. 


**Authentication:**
    
Access to these services is protected by an API key mechanism. Users must provide a valid API key in the request header for authentication.

**How to Use:**
 
- To reset a user: Use the `/reset-user-account/` endpoint, ensuring the provided API key is valid.
  
- To reset all blocked users: Use the `/reset-all-users/` endpoint, ensuring the provided API key is valid.

**Obtaining an API Key:**
    
For users requiring an API key, please contact `M Mansour` for assistance.

"""

app = FastAPI(title="Join Isnad Bot",
              description=description,
              summary="Isnad Tasks - Util API.",
              version="0.0.1", swagger_ui_parameters={"defaultModelsExpandDepth": -1}
              )


@app.on_event("startup")
async def startup_event():
    print('JoinIsnad Multis Server started---- :', datetime.now())
    global is_task_running
    is_task_running = True
    try:
        main()
        pass
    except telegram.error.Conflict as e:
        print(f"Telegram Conflict Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


API_KEY_ADMIN = "iSLgvYQMFbExJGIVpJHEOEHnYxyzT4Fcr5xfSVG2Sn0q5FcrylK72Pgs3ctg0Cyp"


# Define a dictionary to store the mapping of userid to api_key
user_api_key_map = {
    "user1": "Hw1MXuWmKwsG4UXlRITVvS3vkKd5xvkiKD2Z9lXPvXZ5tuUEsTGAfqT8m8AnNGuo",
    "user2": "ERGZdjZqumtfZccYmpYwIlAO83RrqATioi6OUXQI8iiVZtG3xiKBfGgPjqgMwdvw",
    "user3": "WbpClFZ2HnsNgbYBwsoYeVFqUGYu64a71Thj7qHA9xE7ca8zjKFw1rOQzohwVOKX",
    "user4": "wRkBnrIMx20TPYRduKsq3SXfc8WkXh0Pj3H0hGYGJBT7qoXXxYMzTMk4JUqkyMsl",
    "user5": "AfIZUKMWVNo0KDnMdinHqaFIZnDgEWzDBw2PgubmffcQzUj9Lh5WaTz3ilzFx8Dp",
    "user6": "XQ5ihKJl2GqUvMM8O0Fs06UmZy6d0EeF4u3QLAMVbppzJETTul90PhQh7vI9oC4R",
    "user7": "fEpvjfO0oZr4fb3ncjQyAYdOc3DdkiCEhlKfBiNa8biHRHTly2duw20C44QZHBCf",
    "user8": "fKrFNeOwapEe7XrIiTRl9ufMbmxEaNGazYpemjb2VVkS8Z40fYVtgQMC46A26K7o",
    "user9": "wJkclhGS7ROCf13YncA69meOp7sdK5iAp9ofMYxbAUc9Gm7fFJ94Xj8EEnTqIEDq",
    "user10": "RpnNbdW9sN8zVddnuHrsFG0I2VMzY2VBI5tnrHhYqVrXiovvNsqHBNkpwjSwyyJf",
    "user11": "SedkImeAadVNu6TloPajo4ekQohXe5yWAi7aEb7aeeHVOeYqvI464Uj9cVXhjoVF",
    "user12": "onHGZ9U57aYeRWUiwoIpdRK4DVhCybGCQLO6xHXtW4SimPtas3j8f4K6OPpTVCEh",
    "admin": API_KEY_ADMIN
    # Add more users and their corresponding api keys
}


# Dependency to get the userid based on the provided api_key
async def get_api_key(api_key: str = Header(..., description="API key for authentication")):
    """
    Get User ID

    Retrieves the userid based on the provided API key.

    - **api_key**: API key for authentication.

    Returns the corresponding userid.
    """
    for userid, key in user_api_key_map.items():
        if key == api_key:
            return userid
    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Dependency to check the admin API key


def get_admin_api_key(api_key: str = Header(..., description="Admin API key for authentication")):
    if api_key != API_KEY_ADMIN:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key",
        )
    return api_key


# Define a global variable to store the conversation ID counter
conversation_id_counter_facebook = 263

# Define a global variable to store the conversation ID counter
conversation_id_counter_twitter = 398

# Define a global variable to store the conversation ID counter
conversation_id_counter_tiktok = 43

# Set to store blocked user chat IDs
blocked_users = set()

# Define conversation states
SELECT_SOCIAL_PLATFORM, GET_VOICE, GET_PROFILE_LINK,START_SELECTION,START_NEW_USER_VIDEO, BLOCKED = range(6)

welcome_message = "اختار المنصة التي تود العمل عليها في *حملة إسناد*:\n\n"



# Endpoint to reset the user request
@app.post("/reset-user-account/")
async def reset_user_account(
    api_key: str = Depends(get_api_key),
    user_chat_id: str = Query(..., title="User Chat_ID",
                           description="User Chat_id of the user."),
):
    """
    Reset the user if blocked, so he can start new request


    - **user_chat_id**: User Chat_id of the user.

    Returns a confirmation message.
    """
    try:
        user_id_int = int(user_chat_id)  
        return_msg = f'Reset user with chat_id {user_chat_id} successfully'
        if user_id_int in blocked_users:
            blocked_users.remove(user_id_int)
            logger.info('Request from UserID: ' +
                    api_key+f' - Reset user with chat_id {user_chat_id} successfully')
        else:
            return_msg = f'Reset user with chat_id {user_chat_id}, user doesnot exit in the block list.'
            logger.info('Request from UserID: ' +
                    api_key+f' - Reset user with chat_id {user_chat_id}, user doesnot exit in the block list.')
            
        return JSONResponse(content={"message": return_msg}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reset the user: {str(e)}")


# Endpoint to reset the user request
@app.post("/reset-all-users/")
async def reset_all_account(
    api_key: str = Depends(get_admin_api_key)
):
    """
    Reset all blocked users, so they can start new request

    Returns a confirmation message.
    """
    try:
        return_msg = f'Reset all users successfully'
        blocked_users.clear()
            
        return JSONResponse(content={"message": return_msg}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reset users: {str(e)}")



# Define a function to start the conversation
def start(update: Update, context: CallbackContext) -> int:
    # Ask the user to select a social platform
    keyboard = [
        [InlineKeyboardButton("🏷️ طلب عضوية جديد", callback_data='new_option')],
        [InlineKeyboardButton("✏️ عضو بالفعل وأريد تغيير الحساب", callback_data='reset_option')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = "يرجي إختيار أحد الخيارات التالية:\n\n"
    context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message, reply_markup=reply_markup,  parse_mode= 'Markdown')
    return START_SELECTION


# Define a function to start the conversation
def start_selection(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    action_selected = query.data
    if action_selected=='reset_option':
        welcome_message =(
        "توجه للآدمن الموجود في جروب البرو ، أو لآدمن الدعم الفني اللي ضمك للحملة من البداية"+"\n"
        " "+"\n")
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
        # return BLOCKED
    else:
        welcome_message = "فيديو شرح خطوات العضوية:\n\n"
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message)
        context.bot.send_video(chat_id=update.effective_chat.id, video=open('joinIsnad.mp4', 'rb'), supports_streaming=True)
        context.user_data['user_username'] = update.callback_query.from_user.username
        context.user_data['user_chat_id'] = update.callback_query.from_user.id  # Store user's chat ID
        
        welcome_message = "هل شاهدت الفيديو للنهاية بشكل مؤكد؟ اكتب : نعم - لا:\n\n"
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message)
        return START_NEW_USER_VIDEO
    

    # Define a function to start the conversation
def start_new_user_video(update: Update, context: CallbackContext) -> int:
    seen_video = update.message.text
    if seen_video=='لا':
        welcome_message =(
        "يرجى مشاهدة الفيديو لأن أي خطأ في إتمام طلب البوت سوف يفشل استقبال طلبك بشكل نهائي"+"\n"
        " "+"\n")
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
        # return BLOCKED
    elif seen_video=='نعم':
        welcome_message = "اختار المنصة التي تود العمل عليها في *حملة إسناد*:\n\n"
        keyboard = [
            [InlineKeyboardButton("🔴 تويتر", callback_data='Twitter')],
            [InlineKeyboardButton("🔵 فيسبوك / انستجرام", callback_data='Facebook')],
            [InlineKeyboardButton("🟢 تيكتوك", callback_data='TikTok')],
        ]
        print('username:',update.message.from_user.username, ', user_id:', update.message.from_user.id)
        context.user_data['user_username'] = update.message.from_user.username
        context.user_data['user_chat_id'] = update.message.from_user.id  # Store user's chat ID
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message, reply_markup=reply_markup,  parse_mode= 'Markdown')
        return SELECT_SOCIAL_PLATFORM
    else:
        welcome_message =(
        "هل شاهدت الفيديو للنهاية بشكل مؤكد؟  اكتب : نعم - لا "+"\n"
        " "+"\n")
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')

# Define a function to handle button clicks
def button_click(update: Update, context: CallbackContext) -> None:
    return SELECT_SOCIAL_PLATFORM

# Define a function to handle social platform selection
def select_social_platform(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    social_platform = query.data

    # Store the user's social platform choice
    context.user_data['social_platform'] = social_platform

    welcome_message =(
        "*شكراً لتطوعك في إسناد* "+"\n"
        " "+"\n"
        "مرحباً بك، أنا *بوت إسناد الإلكتروني🤖 * لاستقبال الأعضاء الجدد:"+"\n"
        " "+"\n"
        "✅ قبل أي شئ يجب تعمل (اسم مستخدم - USER NAME) لحسابك تليجرام من الإعدادات"+"\n"
        "اعمل دا .. وبعدها كمل قرادة الرساله دي 👇🏼"+"\n"
        " "+"\n"
        "1️⃣-  أول خطوة للانضمام هي الانضمام للجروب المغلق."+"\n"
        " "+"\n"
        "2️⃣-  الانضمام لجروب إسناد بيستلزم نتأكد انك شخص عربي حقيقي."+"\n"
        " "+"\n"
        " "+"\n"
        "3️⃣- لذلك مطلوب منك تبعتلنا هنا رىىىـ.ـــا له فو، ـيس تحكى فيها تحــ ــيةـالىىىــلامــ صو،تياَ وبعدها جملة من 4 كلمات تقول ليه بتنضم لإسناد —- تسجلها من المايك تحت في تليجرام كرد على الرىىىىاله هنا."+"\n"
        " "+"\n"
        "هذه رسالة ثابتة من بوت إسناد الآلي (لست إنسان)"+"\n"
        "فقط مسموح بإرسال التىىىـ. ـجـــل الصو. تى في الرد."+"\n"
        "إرسال أي رسالة فاضية أو غير مطابقة سيتم استبعاد طلبك."+"\n"
        " "+"\n"
        "تحياتنا، ومرحباً بك.✅"+"\n"
    )

    context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('voiceMsgNote.jpeg', 'rb'))
    return GET_VOICE


# Define a function to get the user's email
def get_profile_link(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    profile_link = update.message.text
    # Store the user's profile link based on the selected platform
    context.user_data['profile_link'] = profile_link
    user_chat_id = update.message.chat_id
    twitter_url_pattern = r'^https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+'
    tiktok_url_pattern = r'^https?://(?:www\.)?tiktok\.com/@\w+'
    facebook_instagram_url_pattern = r'^https?://(?:www\.)?(?:facebook|instagram)\.com/\w+'
    url_pattern= ''
    social_emoji= ''
    social_link= ''
    error_msg= ''
    social_platform = context.user_data['social_platform']
    if social_platform=='Twitter':
        url_pattern=twitter_url_pattern
        social_emoji='<b>🔴طلب عضوية جديد تويتر</b>'
        social_link= "<a href=\""+context.user_data['profile_link']+"\">أكونت تويتر</a>"
        error_msg = "عفواً, مسموح فقط بإرسال رابط تويتر يبدأ بـ http بدون أي حروف قبلها."
    if social_platform=='Facebook':
        url_pattern=facebook_instagram_url_pattern
        social_emoji='<b>🔵طلب عضوية جديد فيسبوك / انستجرام</b>'
        social_link= "<a href=\""+context.user_data['profile_link']+"\">أكونت فيسبوك/انستجرام</a>"
        error_msg = "عفواً, مسموح فقط بإرسال رابط أكونت فيس بوك أو انستجرام يبدأ بـ http بدون أي حروف قبلها."
    if social_platform=='TikTok':
        url_pattern=tiktok_url_pattern
        social_emoji='<b>🟢طلب عضوية جديد تيك توك</b>'
        social_link= "<a href=\""+context.user_data['profile_link']+"\">أكونت تيك توك</a>"
        error_msg = "عفواً, مسموح فقط بإرسال رابط أكونت تيك توك يبدأ بـ http بدون أي حروف قبلها."
        
    if re.match(url_pattern, profile_link):
        global conversation_id_counter_twitter  # Access the global conversation ID counter Twitter
        global conversation_id_counter_tiktok  # Access the global conversation ID counter Tiktok
        global conversation_id_counter_facebook  # Access the global conversation ID counter Facebook

        # Generate a unique ID for the conversation
        if social_platform=='Twitter':
            context.user_data['conversation_id'] = conversation_id_counter_twitter
            conversation_id_counter_twitter += 1  # Increment the conversation ID counter
        if social_platform=='Facebook':
            context.user_data['conversation_id'] = conversation_id_counter_facebook
            conversation_id_counter_facebook += 1  # Increment the conversation ID counter
        if social_platform=='TikTok':
            context.user_data['conversation_id'] = conversation_id_counter_tiktok
            conversation_id_counter_tiktok += 1  # Increment the conversation ID counter
        # Forward the voice message along with the user's chatid to the admin
        conversation_id = context.user_data['conversation_id']
        # '5614066882'516506452
        admin_chat_ids = ['5614066882']
        # Forward the data to each admin with a label indicating the social platform
        # admin_chat_ids = ['516506452', '1106597510']  # Replace with your admin's chat IDs

        voice_message_id = context.user_data['voice']['file_id']
        # context.user_data['twitter_account'] = user_twitter_url

        user_username = ""
        if context.user_data['user_username']:
            user_username = str(context.user_data['user_username'])
            admin_msg =(
                social_emoji+"\n"
                " "+"\n"
                "<u>بيانات العضو:</u>"+"\n"
                " "+"\n"
                "رقم العضوية: " + str(conversation_id)+"\n"
                " "+"\n"
                "أكونت تليجرام:"+"\n"
                "@"+user_username+"\n"
                " "+"\n"
                "رقم العضو لإعادة الطلب: " + str(update.message.from_user.id)+"\n"
                " "+"\n"
                " "+ social_link
                )
        else:
            admin_msg =(
                 social_emoji+"\n"
                " "+"\n"
                "<u>بيانات العضو:</u>"+"\n"
                " "+"\n"
                "رقم العضوية: " + str(conversation_id)+"\n"
                " "+"\n"
                "<a href=\"https://web.telegram.org/a/#"+str(update.message.from_user.id)+"\"> تليجرام ويب</a>"
                " "+"\n"
                " "+"\n"
                "<a href=\"tg://user?id="+str(update.message.from_user.id)+"\">أكونت تليجرام</a>"
                " "+"\n"
                " "+"\n"
                "رقم العضو لإعادة الطلب: " + str(update.message.from_user.id)+"\n"
                " "+"\n"
                " "+ social_link
            )
        for admin_chat_id in admin_chat_ids:
            context.bot.send_message(admin_chat_id, admin_msg, parse_mode="HTML", disable_web_page_preview=True)
            context.bot.send_message(admin_chat_id, "<b>الرسالة الصوتية:</b>" , parse_mode="HTML")
            context.bot.send_voice(admin_chat_id, voice=voice_message_id)
            context.bot.send_message(admin_chat_id, "---------------------------------------" , parse_mode="HTML")
        # Block further messages from the user
        blocked_users.add(user_chat_id)

        thanks_message =(
            "<b>✅ طلبك قيد المراجعه من الآدمن المختص</b>"+"\n"
            " "+"\n"
            "سيتم مراجعته والتواصل معك خلال 72 ساعة - برجاء مراجعة رسائلك على الخاص جيداً، وان لم يتم التواصل معك بعد 72 ساعة - <a href=\'https://t.me/ASKisnad_Bot\'>اضغط هنا</a> "+"\n"
            "سنراجع طلبك وفي حال انك ارسلت حساب عبري صحيح، والرسالة التأكيدية بشكل صحيح، سيتم قبول طلبك."+"\n"
            " "+"\n"
            )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')
        thanks_message=(
            "🛑 برجاء عدم تغيير يوزرنيم التليجرام ولا بيانات حساباتك خلال فترة المراجعة وإلا يكون طلبك لاغياً ولا يمكن تكراره."+"\n"
            " "+"\n"
            "سنواجع طلبك وفي حال انك ارسلت حساب عبري صحيح ، والرساله التأكيدية بشكل صحيح، سيتم قبول طلبك."+"\n"
        )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')
        thanks_message=(
            "ونعتذر لتعدد الخطوات ، ولكن هذا لأمان الحملة."+"\n"
            " "+"\n"
            "ـ🇵🇸"
            "لنا طلب أخير عندك بعد انضمامك لنا، ربنا أعطالنا طريقة لإسناد المقاومة ونصرة المظلومين، وأختارنا ليمسح عنا العجز والخذلان :"+"\n"
            " "+"\n"
            "<b>\"نتمنى منك بشدة انك لا تتوقف عن تنفيذ المهمات، ولا يؤثر بك الإحباط أو الألم ، ولا تتخاذل عن استكمال المهمات يوميا، حتى يكتب لنا ربنا النصر ، ويكتب لنا أجر المجاهدين المرابطين \"</b>"+"\n"
            " "+"\n"
            " "+"\n"
            "تحياتنا "+"\n"
            "ومرحب بيك في إسناد "+"\n"
        )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')

        return BLOCKED
    else:
        update.message.reply_text(error_msg)
        return GET_PROFILE_LINK

# Define a function to handle messages from blocked users
def blocked_message_handler(update: Update, context: CallbackContext) -> None:
    user_chat_id = update.message.chat_id
    if user_chat_id in blocked_users:
        context.bot.send_message(chat_id=update.effective_chat.id,text=
            "\"أنا لست إنسان، <b> أنا روبوت </b>، رجاء لا تعيد الخطوات ولا تكرر الخطوات ولا تعمل ريبلاي على رسائلي، ولا تمسح الشات ولا الرسائل ولا تبدأ من البداية ،، فقط ارسل المطلوب والتزم بالخطوات. كما هو موضح في الفيديو بالأعلى، وسيتم التواصل معك\"."
        , parse_mode= 'HTML'
        )
    else:
        # Process the message as usual
        # Ask the user to select a social platform
        keyboard = [
        [InlineKeyboardButton("🔴 تويتر", callback_data='Twitter')],
        [InlineKeyboardButton("🔵 فيسبوك / انستجرام", callback_data='Facebook')],
        [InlineKeyboardButton("🟢 تيكتوك", callback_data='TikTok')],
        ]
        welcome_message = "تم حذف الطلب السابق, يمكنك تقديم طلب جديد. تأكد من إستكمال كل المطلوب لضمان الموافقة علي الطلب."
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
        welcome_message = "اختار المنصة التي تود العمل عليها في *حملة إسناد*:\n\n"
        context.user_data['user_username'] = update.message.from_user.username
        context.user_data['user_chat_id'] = update.message.from_user.id  # Store user's chat ID
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message, reply_markup=reply_markup,  parse_mode= 'Markdown')
        return SELECT_SOCIAL_PLATFORM


# Define a function to get the user's voice message
def get_voice(update: Update, context: CallbackContext) -> int:

    if update.message.voice:
        user = update.message.from_user
        context.user_data['voice'] = update.message.voice
        social_platform = context.user_data['social_platform']
        if social_platform=='Twitter':
            voice_finished_message =(
            "⭕️ <b>مطلوب الآن تعمل حساب صهيوني على تويتر ..هتعمله إزاي ؟</b>"+"\n"
            " "+"\n"
            "<b> أول وأهم حاجة لازم تكون مقرّر هو أكونت بنت ولا ولد وعمره كام، عشان تبني المعلومات عليه </b>  "+"\n"
            "<b> وضروري جدااا  . . العمر ميقلش عن 20 سنة🚫 </b>"+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            voice_finished_message =(
            "1️⃣- تختار إسم عبري بحروف عبرية، من جوجل أو ممكن تختار من هنا (<a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>) - أو ممكن تطلب من CHAT GPT (لو بتستخدمه) يرشحلك اسم اسرائيلي ويكتبه بحروف عبرية، أو انجليزية عادي."+"\n"
            " "+"\n"
            "2️⃣- هتعمل إيميل جوجل جديد والإيميل نفسه تعمله بإسمك اليهودي اللي إختارته، متعملوش عربي عشان مبيتغيرش"+"\n"
            " "+"\n"
            "3️⃣- الصور (لا نستخدم علم إسرائيل نهائياً) إنه مجرد حساب، لا تتقن الدور لهذه الدرجة 😄: "+"\n"
            " "+"\n"
            "*الصورة الشخصية: يفضل تكون لشخص عادي حتى لو من بعيد والملامح مش ظاهرة،"+"\n"
            "ودي ممكن تتجاب من الفيسبوك أو إنستا أو تويتر من أي أكونت أجنبي."+"\n"
            " "+"\n"
            "* الصورة الخلفية: صورة كوڤر عادية جداً، نبعد عن أعلام إسرائيل والحاجات الدينية. "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            voice_finished_message =(
            "4️⃣- الحساب ميكونش فيه ولا كلمة عربي ولا بوست ولا صديق ولا لايك لأي صفحة."+"\n"
            " "+"\n"
            "5️⃣- يكون لوكيشن الحساب إسم الدولة إسرائيل "+"\n"
            " بالإنجليزي Israel  أو بالعبري ישראל"+"\n"
            " "+"\n"
            " ولو طلب رقم تليفونك اثناء عمل الحساب، ومفيش مفر،، ممكن تدخله عادي، الرقم لن يظهر لأي أحد غيرك. ولا مشكلة."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "6️⃣-  الوصف/البايو: ممكن تكتب بالانجليزي ،، أو تاخد بايو عبري من أكاونت صهيوني حقيقي لأي حد من فيسبوك أو إنستا"+"\n"
            " وتخلي بالك تاخده من حساب شبه حسابك (مذكر و لا مؤنث) عشان بتفرق في الصياغة."+"\n"
            " "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "<b> أهم حاجة إن الأكونت يكون متسق مع بعضه مش متناقض، </b>"+"\n"
            "<b> يعني ميبقاش إسم بنت ووصف شاب!🚫 </b>"+"\n"
            "<b> أو صورة شابة صغيرة ومكتوب إنها جدة مثلًا🚫 </b>"+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            voice_finished_message =(
            "اعمل الحساب بالمواصفات دي .. ثم ارسل لنا رابط الحساب هنا ، أرسل الرابط مباشرة بدون عمل ريبلاي على الرسالة."+"\n"
            " "+"\n"
            "عند لصق الرابط في الرد هنا، تأكد انه يبدأ بـ http ولا يسبقها أي حروف أو كلمات"+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        if social_platform=='TikTok':
            voice_finished_message =(
            "📱 <b>الخطوة الجاية عمل حساب تيك توك بالمواصفات دي: </b>"+"\n"
            " "+"\n"
            "اول حاجه ضروري ننزل برنامج ل vpn Israel من المتجر و نشغله واحنا بنعمل الاكونت و بننشر منه، و خلي بالك الvpn مش بيشتغل عالتيك توك من التطبيق، بيشتغل ع المتصفح سواء عالموبايل أو اللابتوب و لو ع اللابتوب أفضل طبعا  "+"\n"
            " "+"\n")
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('joinIsnadTiktok.jpeg', 'rb'))
            voice_finished_message =(
            "ومننساش ضروري نغير البلد و احنا بنعمل الاكونت من الخطوة اللي في الصورة👆و نخليها اسرائيل."+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "2️⃣- الاسم يكون يهودي وينكتب انجليزي او عبري ، والافضل يكون ثنائي مع ايموجي خصوصا لو اسم بنت ، و اليوزر نايم ثنائي انجليزي ، و بلاش موضوع ساره و ليفي و كوهين داه عشان مفقوس اوي 😀 "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML')
            time.sleep(1)
            voice_finished_message =(
            "3️⃣- الصورة تكون لشخص و السيرة الذاتية او البايو تكون عبري و مناسبه لطبيعة التيك توك المرحة مع كام إيموجي "+"\n"
            " "+"\n"
            " و الصورة و الوصف ممكن ناخدهم من اكونت اي حد صهيوني حقيقي على وسائل التواصل، بس خلي بالك انت واخدهم من اكونت ذكر ولا انثي ، عشان صياغة البايو بتفرق من ذكر لأنثي"+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "ودي حسابات قناة مشهورة عندهم ، هنلاقي منهم  هناك في التعليقات ممكن ناخد صور واسامي و وصف منهم و نركبهم علي بعض"+"\n"
            " "+"\n"
            "  <a href=\'https://www.tiktok.com/@n12news\'>اضغط هنا</a>"+"\n"
            "  <a href=\'https://m.facebook.com/N12News\'>أو هنا</a>"+"\n"
            "  <a href=\'https://x.com/N12News?s=20\'>أو هنا</a>"+"\n"
            "او صورة بنت صغيرة و مكتوب انها ام مثلا او جدة.."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            voice_finished_message =(
            "اعمل الحساب بالمواصفات دي .. ثم ارسل لنا رابط الحساب هنا ، أرسل الرابط مباشرة بدون عمل ريبلاي على الرسالة."+"\n"
            "عند لصق الرابط في الرد هنا، تأكد انه يبدأ بـ http ولا يسبقها أي حروف أو كلمات."+"\n"
            " "+"\n"
            )
        if social_platform=='Facebook':
            voice_finished_message =(
            "⭕️ <b>مطلوب الآن تعمل حساب صهيوني على فيسبوك أو انستا ..هتعمله إزاي ؟</b>"+"\n"
            " "+"\n"
            "<b> أول وأهم حاجة لازم تكون مقرّر هو أكونت بنت ولا ولد وعمره كام، عشان تبني المعلومات عليه </b>  "+"\n"
            "<b> وضروري جدااا  . . العمر ميقلش عن 20 سنة🚫 </b>"+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "1️⃣- تختار اسم عبري بحروف عبرية ، من جوجل أو ممكن تختار من هنا <a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>"+"\n"
            "- أو ممكن تطلب من CHAT GPT (لو بتستخدمه) يرشحلك اسم اسرائيلي ويكتبه بحروف عبرية، أو انجليزية عادي. "+"\n"
            "ممكن اسم بحروف انجليزي عادي ،، مش شرط عبري ،، ولو الاتنين مع بعض يكون أفضل. و يكون متجانس مع اليوزرنيم."+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "2️⃣- هتعمل إيميل جوجل جديد والإيميل نفسه تعمله بإسمك اليهودي اللي إختارته، متعملوش عربي عشان مبيتغيرش"+"\n"
            "3️⃣- الصور (منتستخدمش علم إسرائيل نهائياً. "+"\n"
            "* الصورة الشخصية: يفضل تكون لشخص عادي حتى لو من بعيد والملامح مش ظاهرة،"+"\n"
            "* ودي ممكن تتجاب من الفيسبوك أو إنستا أو تويتر من أي أكونت أجنبي. "+"\n"
            " "+"\n"
            "* * الصورة الخلفية: صورة كوڤر عادية جداً، نبعد عن أعلام إسرائيل والحاجات الدينية. "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "4️⃣-  الحساب ميكونش فيه ولا كلمة عربي ولا بوست ولا صديق ولا لايك لأي صفحة."+"\n"
            "5️⃣- يكون لوكيشن الحساب إسم الدولة إسرائيل"+"\n"
            " بالإنجليزي Israel  أو بالعبري ישראל "+"\n"
            " ولو طلب رقم تليفونك اثناء عمل الحساب، ومفيش مفر،، ممكن تدخله عادي، الرقم لن يظهر لأي أحد غيرك. ولا مشكلة."+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "6️⃣-  الوصف/البايو: ممكن تكتب بالانجليزي ،، أو تاخد بايو عبري من أكاونت صهيوني حقيقي لأي حد من فيسبوك أو إنستا"+"\n"
            " "+"\n"
            " وتخلي بالك تاخده من حساب شبه حسابك (مذكر و لا مؤنث) عشان بتفرق في الصياغة."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            voice_finished_message =(
            "<b> أهم حاجة إن الأكونت يكون متسق مع بعضه مش متناقض، </b>"+"\n"
            "<b> يعني ميبقاش إسم بنت ووصف شاب!🚫 </b>"+"\n"
            "<b> أو صورة شابة صغيرة ومكتوب إنها جدة مثلًا🚫 </b>"+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            time.sleep(1)
            voice_finished_message =(
            "اعمل الحساب بالمواصفات دي .. ثم ارسل لنا رابط الحساب هنا ، أرسل الرابط مباشرة بدون عمل ريبلاي على الرسالة."+"\n"
            "عند لصق الرابط في الرد هنا، تأكد انه يبدأ بـ http ولا يسبقها أي حروف أو كلمات."+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        return GET_PROFILE_LINK
    else:
        update.message.reply_text(
            " فقط مسموح بإرسال المطلوب في الرسالة السابقة، أعد قرائتها جيداً ."
        )
        return GET_VOICE

# Define a function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        "The conversation has been canceled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater("6918060750:AAGszCil-X5tkDhYf-DDxklzbhlLAL_Cy98")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_SOCIAL_PLATFORM: [CallbackQueryHandler(select_social_platform)],
            START_SELECTION: [CallbackQueryHandler(start_selection)],
            START_NEW_USER_VIDEO: [MessageHandler(Filters.text & ~Filters.command, start_new_user_video)],
            GET_VOICE: [MessageHandler(Filters.all & ~Filters.command, get_voice)],
            GET_PROFILE_LINK: [MessageHandler(Filters.text & ~Filters.command, get_profile_link)],
            BLOCKED: [MessageHandler(Filters.text & ~Filters.command, blocked_message_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Register conversation handler
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    # updater.idle()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
