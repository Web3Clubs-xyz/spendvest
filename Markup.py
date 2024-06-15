from telebot.types import  InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply, InputMediaVideo

def clear_prev_markup():
    clear_prev_keyboard = ReplyKeyboardRemove(selective=False)
    return clear_prev_keyboard

def prompt_input_markup():
    markup = ForceReply(selective=False)
    return markup


def main_markup():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    browse_btn = KeyboardButton('Browse')
    select_btn = KeyboardButton('Select')
    cancel_btn = KeyboardButton('Cancel')

    markup.add(browse_btn, select_btn, cancel_btn)
    return markup

def wallet_markup():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    refresh_btn = KeyboardButton('Refresh')
    withdraw_btn = KeyboardButton('Withdraw')
    done_btn = KeyboardButton('Done')

    markup.add(refresh_btn, withdraw_btn, done_btn)
    return markup 




