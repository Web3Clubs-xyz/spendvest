from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply

def main_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row_width = 1
    browse_btn = KeyboardButton('Browse')
    select_btn = KeyboardButton('Select')
    cancel_btn = KeyboardButton('Cancel')
    markup.add(browse_btn, select_btn, cancel_btn)
    return markup

def acc_submenu_one():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row_width = 1
    register_btn = KeyboardButton("Register")
    refresh_btn = KeyboardButton("Refresh")
    withdraw_btn = KeyboardButton("Withdraw")
    done_btn = KeyboardButton("Done")
    markup.add(register_btn, refresh_btn, withdraw_btn, done_btn)
    return markup  

def abt_submenu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row_width = 1
    done_btn = KeyboardButton("Done")
    markup.add(done_btn)
    return markup

def clear_prev_markup():
    # Returning an empty markup to clear previous markup
    return ReplyKeyboardRemove()

def force_reply_markup():
    # For forcing a reply from the user
    return ForceReply(selective=False)
