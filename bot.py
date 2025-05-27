import re
import random
import sqlite3
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler # type: ignore
from nigerian_states import NIGERIAN_STATES

# Initialize the database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        address TEXT,
        state TEXT,
        lga TEXT,
        password TEXT,
        referral_code TEXT,
        email TEXT,
        registration_date TEXT,
        bvn TEXT,              
        bank_name TEXT,        
        account_number TEXT,   
        gender TEXT,           
        dob TEXT               
    )
    ''')
    conn.commit()
    conn.close()
    
init_db()

TOKEN = "7077237001:AAGr3WoBn4D3pN9dvohsYII5v-ym5h__ja8"  # Replace with your bot token

# Define Conversation states
FIRST_NAME, LAST_NAME, PHONE, ADDRESS, STATE, LGA, REFERRAL_CODE, OTP_VERIFICATION, PASSWORD,\
CONFIRM_PASSWORD, CONTINUE, EMAIL,\
PHONE_LOGIN, PASSWORD_LOGIN, BVN, BANK_NAME, ACCOUNT_NUMBER, GENDER, DOB, BUY_AIRTIME_PHONE, BUY_AIRTIME_NETWORK,\
BUY_AIRTIME_AMOUNT, BUY_DATA_PHONE, BUY_DATA_PLAN, BUY_DATA,AMOUNT = range(26)

# Email validation pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

keyboard = [
    [InlineKeyboardButton("Register", callback_data="register")],
    [InlineKeyboardButton("Login", callback_data="login")],
    [InlineKeyboardButton("Help", callback_data="help")],
] 
reply_markup = InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "👋 Welcome to *Kadick Integrated Limited*!\n\n"
        "This is the official bot for *KadickMoni* — your trusted platform for *airtime and data vending*, "
        "designed to help agents and customers transact seamlessly.\n\n"
        "💡 What we offer here:\n"
        "• Register as a new agent or user\n"
        "• Get information about your wallet balance\n"
        "• Vend airtime or data\n"
        "• Access support\n\n"
        "To get started, please choose an option below:\n\n"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        'Available commands:\n'
        '/register - Register your details\n'
        '/login - Login to your account\n'
        '/help - Show help\n'
        '/start - Show the welcome message\n'
        '/continue - Proceed to second phase of registration\n'
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
        "📱 Please enter your registered phone number:",
        parse_mode="Markdown"
    )
    else:
        await update.message.reply_text(
            "📱 Please enter your registered phone number:",
        parse_mode="Markdown"
        )
        return PHONE_LOGIN

async def receive_login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw_phone = update.message.text.strip()
    clean_phone = re.sub(r'\D', '', raw_phone)

    if len(clean_phone) != 11 or not clean_phone.isdigit():
        await update.message.reply_text(
            " Invalid phone number format. Please enter 11 digits(e.g 08012345678):"
        )
        return PHONE_LOGIN
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT user_id, password, first_name, last_name FROM users WHERE phone = ?', (clean_phone,))
    user_data = c.fetchone()
    conn.close()

    if not user_data:
        await update.message.reply_text(
            "❌ No account found with this number.\n " 
            "Please register first with /register."
        )
        return ConversationHandler.END
    
    # Store user data for verification
    context.user_data['login_user_id'] = user_data[0]
    context.user_data['stored_password'] = user_data[1]
    context.user_data['first_name'] = user_data[2]
    context.user_data['last_name'] = user_data[3]

    await update.message.reply_text(
        "🔒 Please enter your password:"
    )
    return PASSWORD_LOGIN

async def receive_login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data['login_user_id']
    stored_password = context.user_data['stored_password']
    attempted_password = update.message.text.strip()

    first_name = context.user_data.get('first_name', '')
    last_name = context.user_data.get('last_name', '')

    # Clear temporary login data
    context.user_data.pop('login_user_id', None)
    context.user_data.pop('stored_password', None)
    context.user_data.pop('first_name', None)
    context.user_data.pop('last_name', None)

    if attempted_password == stored_password:
        context.user_data['logged_in'] = True

        keyboard = [
            [InlineKeyboardButton("Services", callback_data="services")],
            [InlineKeyboardButton("My Profile", callback_data="my_profile")],
            [InlineKeyboardButton("Logout", callback_data="logout")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "✅ Login successful!\n\n"
            f"Welcome back, {last_name} {first_name}\n"
            "Your balance:  ₦0.00\n\n"
            "Please select an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Incorrect password. Please try /login again."
        )
        return ConversationHandler.END

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("Buy Airtime", callback_data="buy_airtime")],
        [InlineKeyboardButton("Buy Data", callback_data="buy_data")],
        [InlineKeyboardButton("Other Services", callback_data="other_services")],
        [InlineKeyboardButton("Back", callback_data="back_to_login")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "🔧 Please choose an option:", 
        reply_markup=reply_markup
    )

async def other_services(update: Update, context:ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("Continue", callback_data="continue_registration")],
        [InlineKeyboardButton("Back", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        "You need to continue your registration to have access to other services\n"
        "Click on continue to proceed.",
        reply_markup=reply_markup
        )

async def back_to_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT first_name, last_name FROM users WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()

    if not user_data:
        await query.message.reply_text(
            "❌ User not found. Please login again."
        )
        return
    
    first_name = user_data[0]
    last_name = user_data[1]

    keyboard = [
            [InlineKeyboardButton("Services", callback_data="services")],
            [InlineKeyboardButton("My Profile", callback_data="my_profile")],
            [InlineKeyboardButton("Logout", callback_data="logout")],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
            f"Welcome back, {last_name} {first_name}\n"
            "Your balance:  ₦0.00\n\n"
            "Please select an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text( 
        "📝 Let's start your registration!\n"
        "Please enter your *First Name*",
        parse_mode="Markdown"
    )
        return FIRST_NAME
    else:
        await update.message.reply_text(
        "📝 Let's start your registration!\n"
            "Please enter your *First Name*:",
            parse_mode="Markdown"
        )
    return FIRST_NAME

async def receive_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text(
        "⌨️ Please enter your *Last Name*:",
        parse_mode='Markdown'
    )
    return LAST_NAME

async def receive_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text(
        "📱 Enter your *Phone Number*:",
        parse_mode='Markdown'
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text.isdigit():
        await update.message.reply_text(
            "⚠️ Please enter a valid phone number (digits only):")
        return PHONE
    if len(update.message.text) != 11:
        await update.message.reply_text(
            "⚠️ Phone number must be 11 digits. Please try again:",
            parse_mode='Markdown'
        )
        return PHONE
    context.user_data['phone'] = update.message.text
    await update.message.reply_text(
        "🏠 Enter your *Residential Address*:",
        parse_mode='Markdown'
    )
    return ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['address'] = update.message.text
    states = list(NIGERIAN_STATES.keys())
    keyboard =[ 
        [InlineKeyboardButton(state, callback_data=state)] for state in states
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌍 Select your *State*:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return STATE

async def receive_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
   query = update.callback_query
   await query.answer()
   selected_state = query.data
   context.user_data['state'] = selected_state

   lgas = NIGERIAN_STATES[selected_state]
   keyboard =[ [InlineKeyboardButton(lga, callback_data=lga)] for lga in lgas]
   reply_markup = InlineKeyboardMarkup(keyboard)

   await query.edit_message_text(
       text="🏙️ Now Select your LGA",
       reply_markup=reply_markup,
       parse_mode='Markdown'
       )
   return LGA
   
async def receive_lga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_lga = query.data
    context.user_data['lga'] = selected_lga

    
    keyboard = [[InlineKeyboardButton("Skip Referral", callback_data="Skip Referral")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
    text=f"✅ Selected state: [{context.user_data['state']}]\n"
        f"✅ Selected LGA: {selected_lga}\n\n"
        f"📎 Please enter your *Referral Code* or press 'Skip Referral' ",
         reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return REFERRAL_CODE
        
def generate_otp():
    return str(random.randint(100000, 999999))

async def receive_referral_code(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['referral_code'] = update.message.text.strip()
    user_phone = context.user_data['phone']

    otp = generate_otp()
    context.user_data['otp'] = otp
    
    await update.message.reply_text(
        f"🔐 OTP sent to *{user_phone}* via SMS. Please enter it here: `{otp}` (Demo)",
    parse_mode='Markdown',
    reply_markup=ReplyKeyboardRemove()
    )
    return OTP_VERIFICATION


async def skip_referral_code(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()

    context.user_data['referral_code'] = None

    user_phone = context.user_data['phone']
    otp = generate_otp()
    context.user_data['otp'] = otp


    await update.callback_query.message.reply_text(
        f"🔐 OTP sent to *{user_phone}* via SMS. Please enter it here: `{otp}` (Demo)",
        parse_mode='Markdown'
    )
    return OTP_VERIFICATION

async def verify_otp(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    stored_otp = context.user_data.get('otp')

    if user_input == stored_otp:
        await update.message.reply_text(
            "✅ OTP verified!\n"\
            "Create your password.\n " \
            "Must be at least 8 characters and " \
            "contain at least one special character and one number."
        )
        return PASSWORD
    else:
        await update.message.reply_text("❌ Invalid OTP. Try again.")
        return OTP_VERIFICATION

async def receive_password(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
        password = update.message.text.strip()
        if len(password) < 8 or not re.search(r'[^a-zA-Z0-9\s]', password ) or not re.search('[0-9]', password):
            await update.message.reply_text(
                "⚠️ Password must be at least 8 characters long and include at least one special character and one number. " \
                "Please try again:",
                parse_mode='Markdown'
            )
            return PASSWORD
        context.user_data['password'] = password
        await update.message.reply_text("🔒 Please confirm your password:")
        return CONFIRM_PASSWORD

async def confirm_password(update: Update, context:ContextTypes.DEFAULT_TYPE) -> int:
        confirmed_password = update.message.text.strip()
        original_password = context.user_data.get('password', '')

        if confirmed_password != original_password:
            await update.message.reply_text("❌ Passwords do not match. \
        Please enter your password again.")
            return PASSWORD

        # Save to database
        user_id = update.effective_user.id
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            if c.fetchone():
                await update.message.reply_text(
                    "⚠️ User already exists. Please login with /login.",
                    parse_mode='Markdown'
                )
                conn.close()
                context.user_data.clear()
                return ConversationHandler.END
            
            c.execute('''INSERT INTO users
                (user_id, first_name, last_name, phone, address, 
                state, lga, password, referral_code, email,
                registration_date, bvn, bank_name, account_number, gender, dob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id,
              context.user_data['first_name'],
              context.user_data['last_name'],
              context.user_data['phone'],
              context.user_data['address'],
              context.user_data['state'],
              context.user_data['lga'],
              context.user_data['password'],
              context.user_data['referral_code'],
              context.user_data.get('email', ''),  
              registration_date,
              context.user_data.get('bvn', ''),    
              context.user_data.get('bank_name', ''),
              context.user_data.get('account_number', ''),
              context.user_data.get('gender', ''),
              context.user_data.get('dob', '')
             ))
            conn.commit()
            conn.close()
            
            confirmation = (
                f"✅ *Registration Successful!* 🎉\n\n"
                f"Here are your details:\n"
                f"👤 **Name**: {context.user_data['first_name']} {context.user_data['last_name']}\n"
                f"📞 **Phone**: {context.user_data['phone']}\n"
                f"🏠 **Address**: {context.user_data['address']}\n"
                f"📍 **State**: {context.user_data['state']}\n"
                f"🏙️ **LGA**: {context.user_data['lga']}\n\n"
                f"Thank you for registering with KadickMoni! 💰\n"
                f"Type or click on /continue to proceed."
            )
            await update.message.reply_text(confirmation, parse_mode='Markdown')
            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            print(f"Database error: {str(e)}")
            await update.message.reply_text(
                "⚠️ An error occurred while saving your data. Please try again.",
            parse_mode='Markdown'
            )
            return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❌ Registration cancelled."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def continue_(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "✅ You have now completed your registration.\n\n"
        "You have access to the following features:\n"
        "• Airtime Recharge\n"
        "• Data Recharge\n\n"
        "Click on /login to view your account."
    )
    return CONTINUE

async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
        "Please enter your *Email Address*",
        parse_mode='Markdown'
    )
        return EMAIL
    else:
        await update.message.reply_text(
            "Please enter your *Email Address*",
            parse_mode='Markdown'
            )
        return EMAIL

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not re.match(EMAIL_PATTERN, email):
        await update.message.reply_text(
            "⚠️ Please enter a valid email address (e.g., example@domain.com):",
            parse_mode='Markdown'
        )
        return EMAIL
    context.user_data['email'] = email

    # Update database
    user_id = update.effective_user.id
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''UPDATE users SET email = ? WHERE user_id = ?''',
                 (email, user_id))
        if c.rowcount == 0:
            await update.message.reply_text(
                "⚠️ No user found. Please complete the first phase of registration with /register.",
                parse_mode='Markdown'
            )
            conn.close()
            context.user_data.clear()
            return ConversationHandler.END
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {str(e)}")
        await update.message.reply_text(
            "⚠️ An error occurred while saving your email. Please try again.",
            parse_mode='Markdown'
        )
        return EMAIL
    
    await update.message.reply_text(
        "🔒 Please enter your BVN (11 digits):"
    )
    return BVN

async def receive_bvn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bvn = update.message.text.strip()
    if not bvn.isdigit() or len(bvn) != 11:
        await update.message.reply_text(
        "⚠️ Invalid, BVN must be 11 digits. Try again:"
        )
        return BVN
    
    context.user_data['bvn'] = bvn
    await update.message.reply_text(
        "🏦 Enter your Bank Name:"
    )
    return BANK_NAME

async def receive_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bank_name'] = update.message.text.strip()
    await update.message.reply_text(
        "💳 Please enter your *Bank Account Number* (10 digits)",
        parse_mode='Markdown'
    )
    return ACCOUNT_NUMBER

async def receive_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    acc_num = update.message.text.strip()
    if not acc_num.isdigit() or len(acc_num) < 10:
        await update.message.reply_text(
            "⚠️ Invalid account number. Minimum 10 digits. Try again:"
        )
        return ACCOUNT_NUMBER
    context.user_data['account_number'] = acc_num

    keyboard = [
        [InlineKeyboardButton("Male", callback_data="male")],
        [InlineKeyboardButton("Female", callback_data="female")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👤 Select your Gender:",
        reply_markup=reply_markup)
    return GENDER

async def receive_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    gender = query.data
    context.user_data['gender'] = gender.capitalize()
    
    await query.edit_message_text(
        text=f"✅ Gender selected: {context.user_data['gender']}"
    )

    await query.message.reply_text(
        "🎂 Enter Date of Birth (DD-MM-YYYY):"
    )
    return DOB

async def receive_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        dob = datetime.strptime(update.message.text.strip(), "%d-%m-%Y")
        context.user_data['dob'] = dob.strftime("%d-%m-%Y")
    except ValueError:
        await update.message.reply_text("⚠️ Invalid date format. Use DD-MM-YYYY:"
        )
        return DOB
    
    user_id = update.effective_user.id
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''UPDATE users SET
                  bvn = ?,
                  bank_name = ?,
                  account_number = ?,
                  gender = ?,
                  dob = ?
                  WHERE user_id = ?''',
                  (context.user_data['bvn'],
                   context.user_data['bank_name'],
                   context.user_data['account_number'],
                   context.user_data['gender'],
                   context.user_data['dob'],
                   user_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            "✅ Additional details saved!\n"
        )
    except Exception as e:
        print(f"Database Error:  {str(e)}")
        await update.message.reply_text(
            "⚠️ Error saving details. Please start over."
        )

    context.user_data.clear()
    return ConversationHandler.END

async def start_buy_airtime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📱 Enter the phone number to recharge"
    )
    return BUY_AIRTIME_PHONE

async def receive_airtime_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) != 11:
        await update.message.reply_text(
            "❌Invalid phone number. Please enter an 11-digit phone number."
        )
        return BUY_AIRTIME_PHONE
    
    context.user_data['airtime_phone'] = phone
    keyboard = [
        [InlineKeyboardButton("MTN", callback_data="MTN")],
        [InlineKeyboardButton("Airtel", callback_data="Airtel")],
        [InlineKeyboardButton("Glo", callback_data="Glo")],
        [InlineKeyboardButton("9mobile", callback_data="9mobile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📶 Select your *network provider*:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return BUY_AIRTIME_NETWORK

async def airtime_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_network = query.data
    context.user_data['airtime_network'] = selected_network


    await query.edit_message_text(
        text=f"Selected network: {selected_network}"
    )
    await query.message.reply_text(
        "💰 Enter the *amount to recharge*:",
        parse_mode='Markdown'
    )
    return BUY_AIRTIME_AMOUNT

async def receive_airtime_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = update.message.text.strip()
    if not amount.isdigit() or int(amount) <= 0:
        await update.message.reply_text(
            "Invalid amount.:"
        
        )
        return BUY_AIRTIME_AMOUNT
    context.user_data["airtime_amount"] = amount

    phone = context.user_data.get('airtime_phone')
    selected_network = context.user_data.get('airtime_network')
    amount = context.user_data.get('airtime_amount')

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✅ Airtime purchase successful!\n\n"
        f"📱 Phone: {phone}\n"
        f"📶 Network: {selected_network}\n"
        f"💵 Amount: ₦{amount}\n\n"
        "Thank you for using KadickMoni!\n",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    context.user_data.pop('airtime_phone', None)
    context.user_data.pop('airtime_network', None)
    context.user_data.pop('airtime_amount', None)
    return ConversationHandler.END

async def start_buy_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📱Enter the phone number for *data purchase*:",
        parse_mode='Markdown'
    )
    return BUY_DATA_PHONE

async def receive_data_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) != 11:
        await update.message.reply_text(
            "❌Invalid phone number. Please enter an 11-digit phone number"
        )
        return BUY_DATA_PHONE
    
    context.user_data['data_phone'] = phone
    keyboard = [
        [InlineKeyboardButton("MTN", callback_data="MTN")],
        [InlineKeyboardButton("Airtel", callback_data="Airtel")],
        [InlineKeyboardButton("Glo", callback_data="Glo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📶 Select your network provider",
        reply_markup=reply_markup
    )
    return BUY_DATA_PLAN

async def buy_data_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_network = query.data
    context.user_data['data_network'] = selected_network
    await query.edit_message_text(
        text=f"Selected network: {selected_network}"

    )
    await query.message.reply_text(
        "Select a data plan:\n"
        "1. 1GB - #1000\n"
        "2. 2GB - #2000\n"
        "3. 5GB - #5000\n"
        "4. 10GB - #10000\n"
        "5. 500MB - #500\n"
        )
    return BUY_DATA_PLAN

async def receive_data_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    plan = update.message.text.strip()
    if plan not in ["1", "2", "3", "4", "5"]:
        await update.message.reply_text(
            "❌ Invalid plan selected. Please choose a valid data plan:\n"
        )
        return BUY_DATA_PLAN


async def receive_data_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = update.message.text.strip()
    context.user_data['data_amount'] = amount

    phone = context.user_data.get('data_phone')
    selected_network = context.user_data.get('data_network')
    amount = context.user_data.get('data_amount')
    


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # First phase conversation handler
    conv_handler = ConversationHandler(
        entry_points= [
        CommandHandler("register", register),
        CallbackQueryHandler(register, pattern="^register$")
        ],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_last_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            STATE: [CallbackQueryHandler (receive_state)],
            LGA: [CallbackQueryHandler (receive_lga)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            CONFIRM_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_password)],
            REFERRAL_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_referral_code),
                            CallbackQueryHandler(skip_referral_code, pattern="^Skip Referral$")], 
            OTP_VERIFICATION: [MessageHandler(filters.TEXT &  ~filters.COMMAND, verify_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Login conversation handler
    login_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
           PHONE_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_login_phone)],
           PASSWORD_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_login_password)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Registration phase conversation handler
    registration_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("registration", registration),
            CallbackQueryHandler(registration, pattern="^continue_registration$")
    ],
    states={
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        BVN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bvn)],
        BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bank_name)],
        ACCOUNT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_number)],
        GENDER: [CallbackQueryHandler(receive_gender, pattern="(?i)^male|female$")],
        DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dob)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    buy_airtime_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_buy_airtime, pattern="^buy_airtime$")],
            states={
                BUY_AIRTIME_PHONE:[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_airtime_phone)],
                BUY_AIRTIME_NETWORK: [CallbackQueryHandler(airtime_network)],
                BUY_AIRTIME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_airtime_amount)]

            },
            fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Register handlers
    # application.add_handler(CallbackQueryHandler(register, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(login, pattern="^login$"))
    application.add_handler(CallbackQueryHandler(help, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(services, pattern="^services$"))
    application.add_handler(CallbackQueryHandler(other_services, pattern="^other_services$"))
    application.add_handler(CallbackQueryHandler(back_to_login, pattern="^back_to_login$"))

    # register other han
    application.add_handler(conv_handler)
    application.add_handler(login_conv_handler)
    application.add_handler(registration_conv_handler)
    application.add_handler(buy_airtime_conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("continue", continue_))
    
    print("Kadick Bot is running..... ")
    application.run_polling()

if __name__ == '__main__':
    main()