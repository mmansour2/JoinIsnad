import datetime
import logging
import os
import random
import re
import time
from typing import List, Optional, Tuple

import telegram
from fastapi import BackgroundTasks, FastAPI, HTTPException
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          Filters, MessageHandler, Updater, filters)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="Join Isnad Bot")


@app.on_event("startup")
async def startup_event():
    print('JoinIsnad Multis Server started---- :', datetime.datetime.now())
    global is_task_running
    is_task_running = True
    try:
        main()
        pass
    except telegram.error.Conflict as e:
        print(f"Telegram Conflict Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Define a global variable to store the conversation ID counter
conversation_id_counter_facebook = 1

# Define a global variable to store the conversation ID counter
conversation_id_counter_twitter = 1

# Define a global variable to store the conversation ID counter
conversation_id_counter_tiktok = 1

# Set to store blocked user chat IDs
blocked_users = set()

# Define conversation states
SELECT_SOCIAL_PLATFORM, GET_VOICE, GET_PROFILE_LINK, BLOCKED = range(4)

welcome_message = "اختار المنصة التي تود العمل عليها في *حملة إسناد*:\n\n"


# Define a function to start the conversation
def start(update: Update, context: CallbackContext) -> int:
    # Ask the user to select a social platform
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
        "2️⃣-  الانضمام لجروب إسناد بيستلزم نتأكد انك شخص عربي حقيقي، لأن بيجيلنا طلبات انضمام من صهاينة بيىىىــىحدموا تطبيقات تزجمة، فبنحتاج نفلترها."+"\n"
        " "+"\n"
        " "+"\n"
        "3️⃣- لذلك مطلوب منك تبعتلنا هنا رىىىـ.ـــا له فو، ـيس تحكى فيها تحــ ــيةـالىىىــلامــ صو،تياَ - كرد على الرىىىىاله هنا."+"\n"
        " "+"\n"
        "هذه رسالة ثابتة من بوت إسناد ، سوف تصل إلى الآدمن المختص لمراجعتها ثم الرد عليك"+"\n"
        "فقط مسموح بإرسال التىىىجـــل الصو، تى في الرد."+"\n"
        " "+"\n"
        "تحياتنا، ومرحباً بك.✅"+"\n"
    )

    context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
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
        error_msg = "عفواً, يرجي إرسال رابط أكونت تويتر فقط."
    if social_platform=='Facebook':
        url_pattern=facebook_instagram_url_pattern
        social_emoji='<b>🔵طلب عضوية جديد فيسبوك / انستجرام</b>'
        social_link= "<a href=\""+context.user_data['profile_link']+"\">أكونت فيسبوك/انستجرام</a>"
        error_msg = "عفواً, يرجي إرسال رابط أكونت فيس بوك أو انستجرام فقط."
    if social_platform=='TikTok':
        url_pattern=tiktok_url_pattern
        social_emoji='<b>🟢طلب عضوية جديد تيك توك</b>'
        social_link= "<a href=\""+context.user_data['profile_link']+"\">أكونت تيك توك</a>"
        error_msg = "عفواً, يرجي إرسال رابط أكونت تيك توك فقط."
        
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
        # admin_chat_ids = ['5614066882']
        # Forward the data to each admin with a label indicating the social platform
        admin_chat_ids = ['516506452', '1106597510']  # Replace with your admin's chat IDs

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
            "<b>طلبك قيد المراجعه من الآدمن المختص</b>"+"\n"
            " "+"\n"
            "ساعدنا بالصبر، سنرد عليك خلال 24 ساعه على الأكثر إن شاء الله"+"\n"
            "سنراجع طلبك وفي حال انك ارسلت حساب عبري صحيح، والرسالة التأكيدية بشكل صحيح، سيتم قبول طلبك."+"\n"
            " "+"\n"
            )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')
        thanks_message=(
            "ونعتذر لتعدد الخطوات ، ولكن هذا لأمان الحملة ، لعدم السماح باندساس صهاينة لحساب المهمات."+"\n"
            " "+"\n"
            "ـ🇵🇸"
            "لنا طلب أخير عندك بعد انضمامك لنا، ربنا أعطالنا طريقة لإسناد المقاومة ونصرة المظلومين، وأختارنا ليمسح عنا العجز والخذلان :"+"\n"
            " "+"\n"
            "<b>\"نتمنى منك بشدة انك لا تتوقف عن تنفيذ المهمات، ولا يؤثر بك الإحباط أو الألم ، ولا تتخاذل عن استكمال المهمات يوميا، حتى يكتب لنا ربنا النصر، ويكتب لنا أجر المجاهدين المرابطين\"</b>"+"\n"
            " "+"\n"
            " "+"\n"
            "<b>تأكد من عمل اسم مستخدم USER NAME لحسابك من إعدادات تليجرام </b>"+"\n"
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
        update.message.reply_text(
            "طلبك قيد المراجعه من الآدمن المختص."
        )
    else:
        # Process the message as usual
        pass


# Define a function to get the user's voice message
def get_voice(update: Update, context: CallbackContext) -> int:

    if update.message.voice:
        user = update.message.from_user
        context.user_data['voice'] = update.message.voice
        social_platform = context.user_data['social_platform']
        if social_platform=='Twitter':
            voice_finished_message =(
            "⭕️ <b>مطلوب الآن تعمل حساب عبري على تويتر بأي إيميل،، ازاي ؟</b>"+"\n"
            " "+"\n"
            "1️⃣- تختار اسم عبري بحروف عبرية ، من جوجل او شات جي بي تي أو ممكن تختار أسامي عبرية من هنا <a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>"+"\n"
            "ملاحظة: أول حاجة لازم تكون مقرر اكاونت بنت ولا ولد وعمره كام، عشان تبقى المعلومات متناسقة 👌 "+"\n"
            "ممكن اسم بحروف انجليزي عادي، مش شرط عبري، ولو الاتنين مع بعض يكون أفضل. و يكون متجانس مع اليوزرنيم."+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "2️⃣- تختار صورة بروفايل صهيونية (سيرش جوجل على صورة مناسبة، لا تستخدم علم اسرائيل أصبح مكشوف)"+"\n"
            "* الصورة الشخصية: يفضل تكون لشخص عادي حتي لو من بعيد والملامح مش ظاهرة، و دي ممكن تجيبها من الفيسبوك عندهم. "+"\n"
            "* صورة الخلفية: يفضل تكون بتعبر عن اتجاه ما، مش مجرد صورة عشوائية. "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "3️⃣- ويوزرنيم تويتر يكون رموز وارقام *مايكونش اسم عربي*. "+"\n"
            "4️⃣- الحساب مهم جداً ميكونش فيه ولا كلمه عربي."+"\n"
            "5️⃣- يكون لوكيشن الحساب اسم الدوله اسرائيل بالانجليزي Israel أو اسرائيل بالعبري: ישראל "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "6️⃣- الوصف/البيو: يتاخد من اكاونت صهيوني فيس او تويتر، بس خلي بالك انت حسابك هايكون (ذكر ولا مؤنث) عشان بتفرق في الصياغة، او ممكن تخلي البيو انجليزي."+"\n"
            " "+"\n"
            "🔴 اهم حاجه ان *الاكونت يكون متسق مع بعضه* مش متناقض،، يعني ميبقاش اسم بنت و الوصف شاب 😅"+"\n"
            "او صورة بنت صغيرة و مكتوب انها ام مثلا او جدة.."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "بعد ما تعمل الحساب بالمواصفات دي، ابعت الرابط بتاعه هنا كرد على الرساله دي،"+"\n"
            "ولو عملته بالفعل، راجعه الاول وحسن فيه بحسب المواصفات دي، وابعت الرابط هنا"+"\n"
            " "+"\n"
            "(لو مش عارف تجيب رابط تويتر، انشر تويته عندك عالحساب وهات الرابط بتاعها من الشير)"+"\n"
            " "+"\n"
            "*رابط وليس صورة شاشة*"+"\n"
            )
        if social_platform=='TikTok':
            voice_finished_message =(
            "⭕️ <b>مطلوب الآن تعمل حساب عبري على تيكتوك  بأي إيميل ،، ازاي ؟</b>"+"\n"
            " "+"\n"
            "1️⃣- تختار اسم عبري بحروف عبرية ، من جوجل او شات جي بي تي أو ممكن تختار أسامي عبرية من هنا <a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>"+"\n"
            "ملاحظة: اول حاجة لازم تكون مقرر اكاونت بنت ولا ولد  وعمره كام. عشان تبقى المعلومات متناسقة 👌 "+"\n"
            "ممكن اسم بحروف انجليزي عادي ،، مش شرط عبري ،، ولو الاتنين مع بعض يكون أفضل. و يكون متجانس مع اليوزرنيم."+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "2️⃣- تختار صورة بروفايل صهيونية (سيرش جوجل على صورة مناسبة، لا تستخدم علم اسرائيل أصبح مكشوف)"+"\n"
            "* الصورة الشخصية : يفضل تكون لشخص عادي حتي لو من بعيد والملامح مش ظاهرة ،، وممكن تبحث وجل عن كلمة (سلفي بدون وجه). "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML')
            time.sleep(1)
            voice_finished_message =(
            "3️⃣- *ويوزر نيم حسابك مايكونش اسم عربي.*. "+"\n"
            "4️⃣- الحساب المهم ميكونش فيه ولا كلمه عربي."+"\n"
            "5️⃣- يكون لوكيشن الحساب اسم الدوله اسرائيل بالانجليزي Israel  أو  اسرائيل بالعبري : ישראל "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "6️⃣- الوصف/البيو:  يتاخد من اكاونت صهيوني حقيقي لأي حد ،، بس خلي بالك  انت حسابك هايكون باسم (ذكر و لا مؤنث) عشان بتفرق في الصياغة.. او ممكن انجليزي."+"\n"
            " "+"\n"
            "🔴 اهم حاجه ان *الاكونت يكون متسق مع بعضه* مش متناقض،، يعني ميبقاش اسم بنت و وصف شاب 😅"+"\n"
            "او صورة بنت صغيرة و مكتوب انها ام مثلا او جدة.."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "بعد ما تعمل الحساب بالمواصفات دي - ابعتهلي الرابط بتاعه هنا كرد على الرساله دي."+"\n"
            "ولو عملته بالفعل، راجعه الاول وحسن فيه بحسب المواصفات دي، وابعت الرابط هنا"+"\n"
            " "+"\n"
            "*رابط وليس صورة شاشة*"+"\n"
            )
        if social_platform=='Facebook':
            voice_finished_message =(
            "⭕️ <b>مطلوب الآن تعمل حساب عبري على فيسبوك  بأي إيميل ،، ازاي ؟</b>"+"\n"
            " "+"\n"
            "1️⃣- تختار اسم عبري بحروف عبرية ، من جوجل او شات جي بي تي أو ممكن تختار أسامي عبرية من هنا <a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>"+"\n"
            "ملاحظة: اول حاجة لازم تكون مقرر اكاونت بنت ولا ولد  وعمره كام. عشان تبقى المعلومات متناسقة 👌 "+"\n"
            "ممكن اسم بحروف انجليزي عادي ،، مش شرط عبري ،، ولو الاتنين مع بعض يكون أفضل. و يكون متجانس مع اليوزرنيم."+"\n"
            " "+"\n"
            )
            time.sleep(1)
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
            voice_finished_message =(
            "2️⃣- تختار صورة بروفايل صهيونية (سيرش جوجل على صورة مناسبة، لا تستخدم علم اسرائيل أصبح مكشوف)"+"\n"
            "* الصورة الشخصية : يفضل تكون لشخص عادي حتي لو من بعيد والملامح مش ظاهرة ،، و دي ممكن تتجاب من الفيسبوك عندهم ."+"\n"
            "* الصورة الخلفية : يفضل تكون بتعبر عن اتجاه ما ، مش مجرد صورة عشوائية. "+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "3️⃣- ويوزر نيم حسابك يكون رموز وارقام *مايكونش اسم عربي*. "+"\n"
            "4️⃣- الحساب المهم ميكونش فيه ولا كلمه عربي."+"\n"
            "5️⃣- يكون لوكيشن الحساب اسم الدوله اسرائيل بالانجليزي Israel  أو  اسرائيل بالعبري : ישראל"+"\n"
            " "+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "6️⃣-  الوصف/البيو:  يتاخد من اكاونت صهيوني حقيقي لأي حد ،، بس خلي بالك  انت حسابك هايكون باسم (ذكر و لا مؤنث) عشان بتفرق في الصياغة.. او ممكن انجليزي."+"\n"
            " "+"\n"
            "🔴 اهم حاجه ان *الاكونت يكون متسق مع بعضه* مش متناقض،، يعني ميبقاش اسم بنت و وصف شاب 😅"+"\n"
            "او صورة بنت صغيرة و مكتوب انها ام مثلا او جدة.."+"\n"
            )
            context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
            time.sleep(1)
            voice_finished_message =(
            "بعد ما تعمل الحساب بالمواصفات دي، ابعتهلي الرابط بتاعه هنا كرد على الرساله دي،"+"\n"
            "ولو عملته بالفعل ، راجعه وحسن فيه بحسب المواصفات دي ، وابعت الرابط هنا"+"\n"
            " "+"\n"
            "*رابط وليس صورة شاشة*"+"\n"
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
    updater = Updater("6891296977:AAHnnrMIqq0nLkc0eX9N8pHFnkbSOfDT6vg")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_SOCIAL_PLATFORM: [CallbackQueryHandler(select_social_platform)],
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
