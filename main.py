import datetime
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Command, Text
from funcs import generate_excel_deposites,generate_excel_orders
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
import sqlite3
from typing import List
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
import os, shutil
from aiogram.types.input_file import InputFile
import asyncio
from payment import get_payment_btc, check_status_payment, get_payment_eth,random_with_N_digits

# TOKEN = "1401709439:AAF1G1VbZKEWg8sVs3OcBQ8hL0GeAsePBuY"
TOKEN = "5112615717:AAGx3uwg6kvT7kZF9bVU2ZbuUi4S2zWj3lY"

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users_data(
        id integer PRIMARY KEY,
        user_id integer,
        first_name varchar,
        username varchar,
        balance float default 0.0
    )
    """)
conn.commit()

admin = [748788690,1984827144]


category = CallbackData("category", 'category')
products = CallbackData("products", "products")
purchasing = CallbackData('product', 'id')

category_physical = CallbackData("category_p", 'category')
products_p = CallbackData("products_p", "products")
purchasing_p = CallbackData('product_p', 'id')


deposit_amount = CallbackData('depoist', 'amount', 'type')
check_payment_cd = CallbackData('check', 'pid')
add_codes_item = CallbackData('codes', 'id')
delete_item = CallbackData('delete_item','id')



class Editor(StatesGroup):
    item = State()
    price = State()
class Amount(StatesGroup):
    amount = State()

class Digital(StatesGroup):
    category = State()
    item_id = State()
    name = State()
    price = State()
    code = State()

class Digital_p(StatesGroup):
    category_p = State()
    item_id_p = State()
    name_p = State()
    price_p = State()
    media_p = State()


class Adding(StatesGroup):
    item = State()
    codes = State()

class Sender(StatesGroup):
    message = State()





async def start_keyboard():
    markup = ReplyKeyboardMarkup()
    markup.add("Products🧺")
    markup.add("My balance💵")
    markup.add("Deposit account💵")
    markup.add("Support🆘")

    return markup

async def menu_keyboard():
    markup = ReplyKeyboardMarkup()
    markup.add("Menu🏠")
    return markup

async def delete_item_keyboard():
    cursor.execute("SELECT * FROM digital_items")
    res = cursor.fetchall()
    markup = InlineKeyboardMarkup()
    for i in res:
        markup.add(InlineKeyboardButton(text=i[3],callback_data=delete_item.new(id=i[2])))
    return markup


async def choose_type():
    markup = ReplyKeyboardMarkup()
    markup.add("Physical💳")
    markup.add("Digital📟")
    markup.add("Menu🏠")
    return markup


async def codes_add_item():
    cursor.execute("SELECT * FROM digital_items")
    res = cursor.fetchall()
    print(res)
    markup = ReplyKeyboardMarkup()
    for i in res:
        markup.add(i[3])
    markup.add("Menu🏠")
    return markup


async def choose_category_digital():
    cursor.execute("SELECT DISTINCT CATEGORY FROM digital_items")
    results = cursor.fetchall()
    markup = InlineKeyboardMarkup()
    for i in results:
        markup.add(InlineKeyboardButton(text=i[0], callback_data=category.new(category=i[0])))
    return markup

async def choose_category_physical():
    cursor.execute("SELECT DISTINCT category FROM physical_items")
    results = cursor.fetchall()
    print(results)
    markup = InlineKeyboardMarkup()
    for i in results:
        markup.add(InlineKeyboardButton(text=i[0], callback_data=category_physical.new(category=i[0])))
    return markup


async def products_keyboard_digital(category):
    cursor.execute("SELECT  * FROM digital_items WHERE CATEGORY=?", (category,))
    results = cursor.fetchall()
    markup = InlineKeyboardMarkup()
    for i in results:
        markup.add(InlineKeyboardButton(text=i[3], callback_data=products.new(products=i[2])))

    return markup

async def products_keyboard_physical(category):
    print(category)
    cursor.execute("SELECT * FROM physical_items WHERE category=?", (category,))
    results = cursor.fetchall()
    markup = InlineKeyboardMarkup(row_width=3)
    i=0
    if category == "Driver License":
        i=0
        while i < 48:
            first = InlineKeyboardButton(text=results[i][3],callback_data=products_p.new(products=results[i][2]))
            second = InlineKeyboardButton(text=results[i+1][3],callback_data=products_p.new(products=results[i+1][2]))
            third = InlineKeyboardButton(text=results[i+2][3],callback_data=products_p.new(products=results[i+2][2]))
            markup.row(first,second,third)
            i+=3
        markup.row(InlineKeyboardButton(text=results[-2][3],callback_data=products_p.new(results[-2][2])),InlineKeyboardButton(text=results[-1][3],callback_data=products_p.new(results[-1][2])))
        return markup



    else:
        for i in results:
            markup.add(InlineKeyboardButton(text=i[3], callback_data=products_p.new(products=i[2])))
    return markup

async def category_keyboard():
    markup = ReplyKeyboardMarkup()
    cursor.execute("SELECT DISTINCT CATEGORY FROM physical_items")
    results = cursor.fetchall()
    for i in results:
        markup.add(i[0])
    return markup

async def choose_deposit_type(amount):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Bitcoin(min 12$)', callback_data=deposit_amount.new(amount=amount, type='b')))
    markup.add(InlineKeyboardButton('Ethereum(min 12$)', callback_data=deposit_amount.new(amount=amount, type='e')))
    return markup

async def accept_buying(id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='Buy', callback_data=purchasing_p.new(id=id)))
    return markup

async def check_payment(pid):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Check', callback_data=check_payment_cd.new(pid=pid)))
    return markup


@dp.message_handler(commands=['start', 'menu'])
@dp.message_handler(lambda message: message.text == "Menu🏠",state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.reset_state()
    cursor.execute("SELECT * FROM users_data where user_id=?",(message.from_user.id,))
    if cursor.fetchall():
        await message.answer("""WELCOME TO SCAMILY VALUES,<b>{}</b>!
Here at SCAMILY VALUES you will find EVERYTHING you need to succeed‼️

🤝Here you can automatically buy what you need🤫
🤝If you have any problems - our support is online 24/7!
🤝Good Luck‼️""".format(message.from_user.first_name),parse_mode=types.ParseMode.HTML,
                             reply_markup=await start_keyboard())
    else:
        referrer = message.text.split()
        print(type(referrer))
        print(type(message.from_user.id))
        if len(referrer)>1:
            if int(referrer[1]) != message.from_user.id:
                cursor.execute("INSERT INTO users_data (user_id,first_name,username,referred) values (?,?,?,?)",
                           (message.from_user.id, message.from_user.first_name, message.from_user.username,referrer[1]))
                conn.commit()
            else:
                cursor.execute("INSERT INTO users_data (user_id,first_name,username) values (?,?,?)",
                               (message.from_user.id, message.from_user.first_name, message.from_user.username,))
                conn.commit()
        else:
            cursor.execute("INSERT INTO users_data (user_id,first_name,username) values (?,?,?)",
                       (message.from_user.id, message.from_user.first_name, message.from_user.username,))
            conn.commit()
        await message.answer("""WELCOME TO SCAMILY VALUES,<b>{}</b>!
Here at SCAMILY VALUES you will find EVERYTHING you need to succeed‼️

🤝Here you can automatically buy what you need🤫
🤝If you have any problems - our support is online 24/7!
🤝Good Luck‼""".format(message.from_user.first_name),parse_mode=types.ParseMode.HTML,
                             reply_markup=await start_keyboard())


@dp.message_handler(lambda message: message.text == "Cancel",state='*')
async def show_catalog(message: types.Message,state:FSMContext):
    await state.reset_state()
    await message.answer("Canceled")
    await message.answer("Welcome to our shop,{}".format(message.from_user.first_name),
                         reply_markup=await menu_keyboard())
@dp.message_handler(lambda message: message.text == "cancel",state='*')
async def show_catalog(message: types.Message,state:FSMContext):
    await state.reset_state()
    await message.answer("Canceled")
    await message.answer("Welcome to our shop,{}".format(message.from_user.first_name),
                         reply_markup=await menu_keyboard())


@dp.message_handler(lambda message: message.text == "Support🆘",state='*')
async def show_catalog(message: types.Message,state:FSMContext):
    await state.reset_state()
    await message.answer("Our support: {}".format('@FrankLucas101'))


@dp.message_handler(lambda message: message.text == "Products🧺",state='*')
async def show_catalog(message: types.Message,state:FSMContext):
    await state.reset_state()
    await message.answer("Choose type of items👇", reply_markup=await choose_type())


# showing items



@dp.message_handler(lambda message: message.text == "Digital📟")
async def show_catalog(message: types.Message):
    await message.answer("Choose category", reply_markup=await choose_category_digital())


@dp.callback_query_handler(category.filter())
async def show_products(call: types.CallbackQuery, callback_data: dict):
    category = callback_data.get("category")
    await call.message.edit_text(category, reply_markup=await products_keyboard_digital(category))




@dp.callback_query_handler(products.filter())
async def show_product(call: types.CallbackQuery, callback_data: dict):
    cursor.execute("SELECT * FROM digital_items where item_id =?", (callback_data.get('products'),))
    res = cursor.fetchall()
    cursor.execute("Select * from digital_quantity where item_id=?", (callback_data.get('products'),))
    quantity = cursor.fetchall()
    if len(quantity) < 1:
        await call.message.answer("Now this item is out of stock!", reply_markup=await menu_keyboard())
    else:
        await call.message.edit_text(
            "Do you want buy a {} for {}$\n(available {} pcs)".format(res[0][3], res[0][4], len(quantity)),
            reply_markup=await accept_buying(callback_data.get('products')))


@dp.callback_query_handler(purchasing.filter())
async def show_products(call: types.CallbackQuery, callback_data: dict):
    cursor.execute("SELECT * FROM digital_items where item_id =?", (callback_data.get('id'),))
    item_id = callback_data.get('id')
    res = cursor.fetchall()
    cursor.execute("Select balance from users_data where user_id=?",(call.from_user.id,))
    balance = cursor.fetchone()
    print(res[0][0])
    datas = datetime.datetime.now()
    if balance>res[0][4]:
        cursor.execute("UPDATE users_data SET balance = balance - ? where user_id = ?",(float(res[0][4]),call.from_user.id,))
        cursor.execute("SELECT * FROM digital_quantity where item_id = ?",(item_id,))
        code = cursor.fetchone()
        cursor.execute("DELETE FROM digital_quantity where digital_code = ?",(code[2],))
        cursor.execute("INSERT INTO orders (user_id,username,item_id,name,price,date) VALUES (?,?,?,?,?,?)",
                       (call.from_user.id,call.from_user.username,item_id,res[0][3],res[0][4],datas,))
        conn.commit()

        await call.message.edit_text("Your code:")
        await call.message.answer("{}".format(code[2]))
    else:
        await call.message.answer("You don't have enough money",reply_markup=await menu_keyboard())

#################################################################

@dp.message_handler(lambda message: message.text == "Physical💳")
async def show_catalog(message: types.Message):
    await message.answer("Choose category", reply_markup=await choose_category_physical())



@dp.callback_query_handler(category_physical.filter())
async def show_products(call: types.CallbackQuery, callback_data: dict):
    category = callback_data.get("category")
    if category == 'Driver License':
        await call.message.edit_text("Choose state:",reply_markup=await products_keyboard_physical(category))
    else:
        await call.message.edit_text(category, reply_markup=await products_keyboard_physical(category))




@dp.callback_query_handler(products_p.filter())
async def show_product(call: types.CallbackQuery, callback_data: dict):
    cursor.execute("SELECT * FROM physical_items where item_id =?", (callback_data.get('products'),))
    res = cursor.fetchall()
    dir = res[0][5]
    if len(dir)<2:
        await call.message.answer('Do you want buy a {} for {}$'.format(res[0][3], res[0][4]),
                                        reply_markup=await accept_buying((callback_data.get('products'))))

    else:
        img = InputFile('media/{}'.format(res[0][5]))
        await call.message.answer_photo(img,'Do you want buy a {} for {}$'.format(res[0][3],res[0][4]),reply_markup=await accept_buying((callback_data.get('products'))))




@dp.callback_query_handler(purchasing_p.filter())
async def show_products(call: types.CallbackQuery, callback_data: dict):
    cursor.execute("SELECT * FROM physical_items where item_id =?", (callback_data.get('id'),))
    item_id = callback_data.get('id')
    res = cursor.fetchall()
    cursor.execute("Select balance from users_data where user_id=?", (call.from_user.id,))
    balance = cursor.fetchone()
    print(res[0][0])
    print(balance)
    datas = datetime.datetime.now()
    if float(balance[0]) > res[0][4]:
        cursor.execute("UPDATE users_data SET balance = balance - ? where user_id = ?",
                       (float(res[0][4]), call.from_user.id,))
        cursor.execute("INSERT INTO orders (user_id,username,item_id,name,price,date) VALUES (?,?,?,?,?,?)",
                       (call.from_user.id, call.from_user.username, item_id, res[0][3], res[0][4], datas,))
        conn.commit()

        await call.message.edit_reply_markup(None)
        await call.message.answer("Write to our administration to get your product @FrankLucas101")
    else:
        await call.message.answer("You don't have enough money", reply_markup=await menu_keyboard())


async def ref_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Get my referral link',callback_data='referral_link'))
    return markup


@dp.message_handler(lambda message: message.text == "My balance💵", state='*')
async def show_catalog(message: types.Message):
    cursor.execute("SELECT balance FROM users_data where user_id =?",(message.from_user.id,))
    balance = cursor.fetchone()
    cursor.execute("SELECT referred FROM users_data where referred = ?",(message.from_user.id,))
    referred = cursor.fetchall()
    print(referred)
    await message.answer("💰Your balance: {}$\n🙎Referred users:{}".format(balance[0],len(referred)),reply_markup=await ref_keyboard())




@dp.callback_query_handler(lambda c: c.data == 'referral_link')
async def process_callback_button1(call: types.CallbackQuery):
    ref_link = 'https://telegram.me/{}?start={}'
    bot_d = await bot.get_me()
    await call.message.edit_text(text=ref_link.format(bot_d['username'], call.from_user.id))


#Deposit system
@dp.message_handler(lambda message: message.text == "Deposit account💵", state='*')
async def show_catalog(message: types.Message):
    await message.answer('Write the amount of the deposit in $',reply_markup=await menu_keyboard())
    await Amount.amount.set()


@dp.message_handler(state=Amount.amount, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    if message.text.title().isdigit():
        if int(message.text.title()) >= 12:
            amount = message.text.title()
            await message.answer("Choose type of items👇", reply_markup=await choose_deposit_type(amount))
            await state.finish()
        else:
            await message.answer("Minimal amount is 12$, write new amount!")
            await Amount.amount.set()
    else:
        await message.answer("Write only digits!")
        await Amount.amount.set()



@dp.callback_query_handler(deposit_amount.filter())
async def checking_payment(call: types.CallbackQuery, callback_data: dict):
    amount = callback_data.get('amount')
    type = callback_data.get('type')
    if type == 'b':
        address, pid, btc = get_payment_btc(amount, call.from_user.id)
        await call.message.edit_text('Send {} to '.format(btc))
        await call.message.answer(address, reply_markup=await check_payment(pid))
    if type == 'e':
        address, pid, eth = get_payment_eth(amount, call.from_user.id)
        await call.message.edit_text('Send {} to '.format(eth))
        await call.message.answer(address, reply_markup=await check_payment(pid))

@dp.callback_query_handler(check_payment_cd.filter())
async def checking_payment(call: types.CallbackQuery, callback_data: dict):
    pid = callback_data.get('pid')
    check_s = check_status_payment(pid)
    print(check_s)
    datas = datetime.datetime.now()
    if(check_s[0] == True):
        cursor.execute("UPDATE users_data SET balance = balance + (?) WHERE user_id=?",(check_s[1],call.from_user.id,))
        conn.commit()
        cursor.execute("SELECT referred FROM users_data where user_id=? ",(call.from_user.id,))
        referred = cursor.fetchone()
        if referred:
            cursor.execute("UPDATE users_data SET balance = balance * (?) where user_id=?",(check_s[1]*1.05,referred[0],))
            conn.commit()
        cursor.execute("INSERT INTO deposit(pid,user_id,amount,data) VALUES (?,?,?,?)",(pid,call.from_user.id,check_s[1],datas))
        conn.commit()
        await call.message.answer('{}$ is deposited to your account'.format(check_s[1]),reply_markup=await menu_keyboard())
        await call.message.delete()

    else:
        await call.answer("Payment status is {}".format(check_s[1]))


#addding item

@dp.message_handler(commands=['add_item_digital'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Write category of item or choose it below",reply_markup=await category_keyboard())
        await Digital.category.set()


@dp.message_handler(state=Digital.category, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    await state.update_data(cat = message.text)
    print(message.text)

    await message.answer("Write id of product",reply_markup=ReplyKeyboardRemove())
    await Digital.item_id.set()


@dp.message_handler(state=Digital.item_id, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    if message.text.title().isdigit():
        item_id = message.text.title()
        cursor.execute("SELECT * FROM digital_items WHERE item_id=?",(item_id,))
        res = cursor.fetchall()
        if res:
            await message.answer("This id is exists, write another one!")
            await Digital.item_id.set()
        else:
            await state.update_data(item_id = message.text.title())
            await message.answer("Write name of product")
            await Digital.name.set()
    else:
        await message.answer("Write only digits")
        await Digital.item_id.set()

@dp.message_handler(state=Digital.name, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.title())
    await message.answer("Write price of product")
    await Digital.price.set()



@dp.message_handler(state=Digital.price, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    if message.text.title().isdigit():
        await state.update_data(price=message.text.title())
        await message.answer("Write code like this()\ncode1 code2 code3 code4\n(separate them by space)")
        await Digital.code.set()
    else:
        await message.answer("Write only digits")
        await Digital.price.set()


@dp.message_handler(state=Digital.code, content_types=types.ContentTypes.TEXT)
async def get_amount(message: types.Message, state: FSMContext):
    datas = await state.get_data()
    codes = message.text.title().split()
    cursor.execute("INSERT INTO digital_items (category,item_id,name,price) VALUES (?,?,?,?)",
                   (datas['cat'],datas['item_id'],datas['name'],datas['price']))
    conn.commit()
    for i in codes:
        cursor.execute("INSERT INTO digital_quantity (item_id,digital_code) values (?,?)",(datas['item_id'],i))
    conn.commit()
    await state.finish()
    await message.answer("Item addded!",reply_markup=await menu_keyboard())




@dp.message_handler(commands=['add_item_physical'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Write category of item or choose it below",reply_markup=await category_keyboard())
        await Digital_p.category_p.set()


@dp.message_handler(state=Digital_p.category_p, content_types=types.ContentTypes.TEXT)
async def get_cat(message: types.Message, state: FSMContext):
    await state.update_data(cat = message.text)
    await message.answer("Write id of product",reply_markup=ReplyKeyboardRemove())
    await Digital_p.item_id_p.set()


@dp.message_handler(state=Digital_p.item_id_p, content_types=types.ContentTypes.TEXT)
async def get_id(message: types.Message, state: FSMContext):
    if message.text.title().isdigit():
        item_id = message.text.title()
        print("p#")
        cursor.execute("SELECT * FROM physical_items WHERE item_id=?",(item_id,))
        res = cursor.fetchall()
        if res:
            await message.answer("This id is exists, write another one!")
            await Digital.item_id.set()
        else:
            await state.update_data(item_id = message.text.title())
            dl = await state.get_data()
            if dl['cat'] == 'Driver License':
                await message.answer("Write state")
                await Digital_p.name_p.set()
            else:
                await message.answer("Write name of product")
                await Digital_p.name_p.set()
    else:
        await message.answer("Write only digits")
        await Digital_p.item_id_p.set()

@dp.message_handler(state=Digital_p.name_p, content_types=types.ContentTypes.TEXT)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.title())
    await message.answer("Write price of product")
    print('#p#p')
    await Digital_p.price_p.set()



@dp.message_handler(state=Digital_p.price_p, content_types=types.ContentTypes.TEXT)
async def get_price(message: types.Message, state: FSMContext):
    if message.text.title().isdigit():
        await state.update_data(price=message.text.title())
        await message.answer("Send photo")
        await Digital_p.media_p.set()
        print('#p#p#p')
    else:
        await message.answer("Write only digits")
        await Digital_p.price_p.set()


@dp.message_handler(state=Digital_p.media_p, content_types=types.ContentTypes.PHOTO)
async def get_photo(message: types.Message, state: FSMContext):
    datas = await state.get_data()
    name_photo = "{}.png".format(random_with_N_digits(6))
    await message.photo[-1].download(name_photo)
    src = "media/" + name_photo
    shutil.move(name_photo, src)
    cursor.execute("INSERT INTO physical_items (category,item_id,name,price,media) VALUES (?,?,?,?,?)",(datas['cat'],datas['item_id'],datas['name'],datas['price'],name_photo))
    conn.commit()
    await message.answer("done",reply_markup=await menu_keyboard())
    await state.finish()


@dp.message_handler(commands=['delete_items'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Choose what product delete",reply_markup=await delete_item_keyboard())

@dp.callback_query_handler(delete_item.filter())
async def show_products(call: types.CallbackQuery, callback_data: dict):
    item_id = callback_data.get('id')
    cursor.execute("DELETE FROM digital_items where item_id =?",(item_id,))
    cursor.execute("DELETE FROM digital_quantity where item_id =?",(item_id,))
    conn.commit()
    await call.message.edit_text("Deleted")


async def edit_price_keyboard():
    cursor.execute("SELECT * FROM digital_items")
    res = cursor.fetchall()
    markup = ReplyKeyboardMarkup()
    for i in res:
        markup.add(i[3])
    return markup


@dp.message_handler(commands=['edit_price'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Choose what product edit price",reply_markup=await edit_price_keyboard())
        await Editor.item.set()


@dp.message_handler(state=Editor.item, content_types=types.ContentTypes.TEXT)
async def get_code(message: types.Message, state: FSMContext):
    cursor.execute("SELECT * from digital_items where name = ?",(message.text,))
    last_price = cursor.fetchone()
    await state.update_data(id=last_price[2])
    await message.answer("Last price is {}\nWrite new price".format(last_price[4]))
    await Editor.price.set()

@dp.message_handler(state=Editor.price, content_types=types.ContentTypes.TEXT)
async def get_code(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        id = await state.get_data()
        cursor.execute("Update digital_items SET price=? where item_id=?",(message.text,id['id'],))
        conn.commit()
        await message.answer("Price is changed",reply_markup=await menu_keyboard())
        await state.finish()
    else:
        await message.answer("Write in digits!")
        await Editor.price.set()


#adding codes


@dp.message_handler(commands=['add_codes_item'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Choose for what item add",reply_markup=await codes_add_item())
        await Adding.item.set()



@dp.message_handler(state=Adding.item, content_types=types.ContentTypes.TEXT)
async def get_item(message: types.Message, state: FSMContext):
    cursor.execute("Select item_id from digital_items where name = ?",(message.text,))
    item_id = cursor.fetchall()
    await state.update_data(item_id = item_id[0][0])
    await message.answer("Write code like this()\ncode1 code2 code3 code4\n(separate them by space)")
    await Adding.codes.set()


@dp.message_handler(state=Adding.codes, content_types=types.ContentTypes.TEXT)
async def get_code(message: types.Message, state: FSMContext):
    item_id = await state.get_data()
    codes = message.text.title().split()
    print(item_id)
    for i in codes:
        cursor.execute("INSERT INTO digital_quantity(item_id,digital_code) VALUES (?,?)",(item_id['item_id'],i,))
    conn.commit()
    await message.answer("Codes added!")
    await state.finish()

@dp.message_handler(commands=['spam_messages'])
async def add_item(message: types.Message):
    if message.from_user.id in admin:
        await message.answer("Write spam message")
        await Sender.message.set()

@dp.message_handler(commands=['get_report_deposites'])
async def add_item(message: types.Message):
    excel = generate_excel_deposites()
    await message.answer_document(open(excel, 'rb'))


@dp.message_handler(commands=['get_report_orders'])
async def add_item(message: types.Message):
    excel = generate_excel_orders()
    await message.answer_document(open(excel, 'rb'))

@dp.message_handler(commands=['help'],state='*')
async def help(message: types.Message,state: FSMContext):
    await state.reset_state()
    if message.from_user.id in admin:
        await message.answer("""/add_item_digital add item to section Digital
        /delet_item deletes item from shop, be careful deletes all codes
        /edit_price edits price of item
        /add_codes_item addes codes to exists item
        /spam_messages sends message to all users of shop
        /get_report_deposites get excel of deposites
        /get_report_orders get excel of orders
        /add_item_physical for add physical item
        
        """)

@dp.message_handler(state=Sender.message, content_types=types.ContentTypes.TEXT)
async def get_code(message: types.Message, state: FSMContext):
    cursor.execute("SELECT user_id from users_data")
    users = cursor.fetchall()
    for i in users:
        await bot.send_message(i[0],message.text)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
