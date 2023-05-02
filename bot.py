#!/usr/bin/env python
import time
from func import bot_config as config

bot_tron_address = config.bot_address
bot_token = config.bot_token
group_url = config.group_url
boss_url = config.boss_url
commission = config.commission

from telegram import (
    Update,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from func.mysql_func import select_last_advance,sum_order_usdt_amount,create_advance_order
from func.func import (
    check_address,
    get_trx_rate,get_trading_order_in_okex,
    account_info,account_token_trc20_usdt,
)

import json
import requests
# 常量
(
    START,
    BANK,
    ALIPAY,
    WXPAY,
    ALL,
    TRADE,
    USDT_PRICE,
    ADVANCE,
) = map(chr, range(8))
END = ConversationHandler.END


#查波场账号信息
def check_tron_account(address:str) ->dict:
    # url = f"https://api.trongrid.io/v1/accounts/"+address
    url = config.trongrid_api+address
    # print(url)
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    account = {"trx":0,"usdt":0}
    res = json.loads(response.text)
    if res.get("data") is not None and bool(res["data"]):
        if res["data"][0].get("balance") :
            account["trx"] = res["data"][0]["balance"] / 1_000_000
        if res["data"][0].get("trc20"):
            for i in res["data"][0]["trc20"]:
                if i.get(config.usdt_address):
                    account["usdt"] = float(i[config.usdt_address]) / 1_000_000
    return account
#管理员id


 


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id < 0:
        return ""
    buttons = [
        # 选择按钮后跳到指定方法 advance
        [
            KeyboardButton("📈实时汇率", callback_data=str("TRX_RATE")),
            KeyboardButton("💸兑换地址", callback_data=str("TRADE_ADDRESS")),
            KeyboardButton("💰预支trx", callback_data=str("ADVANCE")),
        ],
        [
            KeyboardButton("‍💁‍♀代开会员", callback_data=str("VIP")),
            KeyboardButton("💹实时OTC", callback_data=str("USDT_PRICE")),
            KeyboardButton("👨‍💼联系老板", callback_data=str("BOSS")),
        ]
    ]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(text="你好，欢迎使用TRX全自动兑换机器人",reply_markup=keyboard)
    return 
    
#开始
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    #问候语
    if update.message.chat_id < 0:
        return ""
    await forward(update,context)
    # print(update)
    first_name = update.message.from_user.first_name
    buttons = [
        # 选择按钮后跳到指定方法 advance
        [
            KeyboardButton("📈实时汇率", callback_data=str("TRX_RATE")),
            KeyboardButton("💸兑换地址", callback_data=str("TRADE_ADDRESS")),
            KeyboardButton("💰预支trx", callback_data=str("ADVANCE")),
        ],
        [
            KeyboardButton("‍💁‍♀代开会员", callback_data=str("VIP")),
            KeyboardButton("💹实时OTC", callback_data=str("USDT_PRICE")),
            KeyboardButton("👨‍💼联系老板", callback_data=str("BOSS")),
        ]
    ]
    last_name = update.message.from_user.last_name
    text = (
        f"{first_name},你好，欢迎使用TRX全自动兑换机器人"
    )
    if update.message.chat_id == config.group_id or update.message.chat_id > 0:
        keyboard = ReplyKeyboardMarkup(buttons,resize_keyboard=True)
        await update.message.reply_text(text=text, reply_markup=keyboard)

    bot_account_balance = check_tron_account(bot_tron_address)
    _trx_rate = get_trx_rate()
    text = (
        f"<b>实时汇率（1U起兑）</b>\n"
        f"100USDT = {round(_trx_rate * 100, 2)} TRX\n\n"
        f"<b>剩余兑换额度:</b>\n"
        f"💸<b>{round(bot_account_balance['trx']/_trx_rate,1)} USDT</b>\n\n"
        f"<b>自动兑换地址:</b>\n"
        f"<code>{bot_tron_address}</code>\n"
        f"(点击地址自动复制)\n\n"
        f"🔸<b>Trx默认回原地址, 其他地址请提前说明</b>\n"
        f"🔸<b>请勿使用交易所或中心化钱包, 丢失自负</b>\n"
        f"🔸<b>交易经过19次网络确认,过程大概60秒</b>\n"
    )
    await update.message.reply_text(text=text,parse_mode="HTML")

    return START
    
#返回调用的菜单
async def start2(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    #问候语
    if update.message.chat_id < 0:
        return ""
    await forward(update,context)
    # print(update)
    first_name = update.message.from_user.first_name
    buttons = [
        # 选择按钮后跳到指定方法 advance
        [
            KeyboardButton("📈实时汇率", callback_data=str(" ")),
            KeyboardButton("💸兑换地址", callback_data=str("TRADE_ADDRESS")),
            KeyboardButton("💰预支trx", callback_data=str("ADVANCE")),
        ],
        [
            KeyboardButton("‍💁‍♀代开会员", callback_data=str("VIP")),
            KeyboardButton("💹实时OTC", callback_data=str("USDT_PRICE")),
            KeyboardButton("👨‍💼联系老板", callback_data=str("BOSS")),
        ]
    ]
    text = (
        f"{first_name},你好，欢迎使用TRX全自动兑换机器人"
    )
    if update.message.chat_id == config.group_id or update.message.chat_id > 0:
        keyboard = ReplyKeyboardMarkup(buttons,resize_keyboard=True)
        await update.message.reply_text(text=text, reply_markup=keyboard)
    return START
    
#实时汇率
async def trx_rate(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    _trx_rate = get_trx_rate()
    bot_account_balance = check_tron_account(bot_tron_address)
    text = (
        f"<b>实时汇率（1U起兑）</b>\n"
        f"100USDT = {round(_trx_rate * 100, 2)} TRX\n\n"
        f"<b>剩余兑换额度</b>\n"
        f"💸<b>{round(bot_account_balance['trx']/_trx_rate,1)} USDT</b>\n\n"
        f"<b>自动兑换地址:</b>\n"
        f"<code>{bot_tron_address}</code>\n"
        f"(点击地址自动复制)\n\n"
        f"<b>注意:</b>\n"
        f"🔸<b>请勿使用交易所或中心化钱包, 丢失自负</b>\n"
        f"🔸<b>交易经过19次网络确认,过程大概60秒</b>\n"
    )
    # inline_buttons = [
    #     [
    #         InlineKeyboardButton("💁‍♀担保公群", url=group_url),
    #         InlineKeyboardButton("🏠私聊老板", url=boss_url),
    #     ],
    # ]
    # keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
    await update.message.reply_text(text=text, parse_mode="HTML")
    return ""
    
#召唤trx
async def trx_ratea(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    _trx_rate = get_trx_rate()
    bot_account_balance = check_tron_account(bot_tron_address)
    text = (
        f"<b>实时汇率（1U起兑）</b>\n"
        f"100USDT = {round(_trx_rate * 100, 2)} TRX\n\n"
        f"<b>剩余兑换额度</b>\n"
        f"💸<b>{round(bot_account_balance['trx']/_trx_rate,1)} USDT</b>\n\n"
        f"<b>自动兑换地址:</b>\n"
        f"<code>{bot_tron_address}</code>(点击地址自动复制)\n\n"
        f"<b>注意:</b>\n"
        f"🔸<b>请勿使用交易所或中心化钱包, 丢失自负</b>\n"
        f"🔸<b>交易经过19次网络确认,过程大概60秒</b>\n"
    )
    # inline_buttons = [
    #     [
    #         InlineKeyboardButton("💁‍♀担保公群", url=group_url),
    #         InlineKeyboardButton("🏠私聊老板", url=boss_url),
    #     ],
    # ]
    # keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
    await update.message.reply_text(text=text, parse_mode="HTML")
    return ""
    
 
    
    
#兑换地址
async def trade_address(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    text = (
        f"<b>自动兑换地址:</b>\n"
        f"<code>{bot_tron_address}</code>\n"
        f"(点击地址自动复制)\n\n"
    )
    await update.message.reply_text(text=text, parse_mode="HTML")
    return ""

#联系老板
async def boss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward(update, context)
    text = (
         f"<b>点下方按钮联系老板：</b>\n"
    )
    inline_buttons = [
        [
            InlineKeyboardButton("双向点我", url=group_url),
            InlineKeyboardButton("直接私聊", url=boss_url),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
    await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    return ""

#代开会员
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward(update, context)
    text = (
        f"<b>请选择充值套餐</b>\n"
    )
    inline_buttons = [
        [InlineKeyboardButton("3个月 售价：15.0U", url=boss_url)],
        [InlineKeyboardButton("6个月 售价：20.0U", url=boss_url)],
        [InlineKeyboardButton("12个月 售价：30.0U", url=boss_url)],
    ]
    keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
    await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    return ""

#预支trx
async def advance(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    if update.message.chat_id < 0:
        return ""
    await forward(update, context)
    text = (
        f"预支TRX规则：\n"
        f"累计兑换超过10U，且钱包里的TRX少于14个。\n"
        f"预支之后即清零，下次预支需要再累计10U的额度。\n"
        f"此外，下次兑换将扣除预支内容。\n\n"
        f"👇👇输入您的波场地址:\n"
    )
    await update.message.reply_text(text=text,quote=True)
    return ADVANCE




#计算公式
async def jisuan(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    address = update.message.text
    jieguo = eval(address)
    text = (
        f"<b>计算结果:{jieguo}</b>\n\n"
        f"<code>{address}={jieguo}</code>\n"
    )
    await update.message.reply_text(text=text, parse_mode="HTML")
    return ""  



#查询余额
async def check_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id < 0 :
        return END
    address = update.message.text
    # if address == config.bot_address:
    #     return TRADE
    if not check_address(address):
        return END
    account = account_info(address)
    context.user_data["info"] = account
    text = (
        f"<b>检测地址:</b>\n"
        f"{address}\n"
        f"<b>USDT余额:</b>{account['usdt']} \n"
        f"<b>TRX余额:</b>{account['trx']}  \n"
        f"<b>TRX质押:</b>{account['delegate_frozen_for_energy']}\n"
        f"<b>带宽:</b>{account['free_net_remaining']}/{account['free_net_limit']} \n"
        f"<b>能源:</b>{account['energy_remaining']}/{account['energy_limit']} \n"
        f"<b>交易次数:</b>{account['transactions']} \n"
        f"<b>    -出:</b>{account['transactions_out']} \n"
        f"<b>    -入:</b>{account['transactions_in']} \n"
        f"<b>地址创建时间:</b>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(account['date_created']/1000))} \n"
        f"<b>地址活动时间:</b>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(account['latest_operation_time']/1000))} \n"

    )
    buttons = [
        [
            KeyboardButton(text="🔍查看近期交易"),
            KeyboardButton(text="↩️返回"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    #keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True,one_time_keyboard=True)
    #keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
    await update.message.reply_text(text=text,parse_mode="HTML",reply_markup=keyboard)
    return TRADE
          
async def account_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id < 0:
        return END
    account = context.user_data["info"]
    address = account["address"]
    data = account_token_trc20_usdt(address)
    # await update.callback_query.answer()
    text = (
        f"余额:{account['usdt']}\n"
        f"总交易次数:{account['transactions']} \n"
        f"总转入笔数:{account['transactions_out']} \n"
        f"总转出笔数:{account['transactions_in']} \n\n"
        f"最近转入记录:\n"
    )
    s = ""
    for _in in data["in"]:
        s += f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(_in['block_ts']/1000))} + " \
            f"{_in['amount']} <a href='https://tronscan.org/#/transaction/{_in['transaction_id']}'>转账详情</a>\n"
    text += s
    text += (
        f"\n最近转出记录\n\n"
    )
    s = ""
    for _in in data["out"]:
        s += f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(_in['block_ts']/1000))} - " \
            f"{_in['amount']} <a href='https://tronscan.org/#/transaction/{_in['transaction_id']}'>转账详情</a>\n"

    text += s
    text += (
        f"\n这里只显示最近20笔USDT交易\n"
        f"👉<a href='https://tronscan.org/#/address/{address}/transfers'>点击查看详细信息</a>"
    )
    # await update.callback_query.edit_message_text(text=text, parse_mode="HTML",disable_web_page_preview=True)
    await  update.message.reply_text(text=text, parse_mode="HTML",disable_web_page_preview=True)
    return TRADE

#预支
async def create_advance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id < 0:
        return END
    await forward(update, context)
    address = update.message.text

    if address == config.bot_address:
        await update.message.reply_text(text="不能预支", quote=True)
        return END

    if not check_address(address):
        await update.message.reply_text(text="无效地址", quote=True)
        return END
    """
    预支TRX规则：累计兑换超过10U，且钱包里的TRX少于14个。预支之后即清零，下次预支需要再累计10U的额度。此外，下次兑换将扣除预支内容。
    """
    text = (
        "不符合预支条件"
    )
    # 查用户地址的兑换记录
    tron_account = check_tron_account(address)
    if tron_account["trx"] > 14:
        await update.message.reply_text(text=text,quote=True)
        return END

    last_advance = select_last_advance(address)
    begin = 0
    if bool(last_advance):
        begin = last_advance["id"]
    history_order_amount = sum_order_usdt_amount(address=address,begin=begin)
    if history_order_amount["sum"]> 10:
        create_advance_order(address=address)
        await update.message.reply_text(text="预支订单已经生成，稍后为您转账", quote=True)
        return END

    await update.message.reply_text(text=text, quote=True)
    return END
 
#otc实时价格
async def usdt_price(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    data = get_trading_order_in_okex()
    if data.get("sell") is not None:
        i = 0
        text = "<b>OKX OTC商家实时汇率 TOP 10</b>\n\n"
        for item in data["sell"]:
            i = i + 1
            if i > 10:
                break
            #print(item) 
            text += f"{i}) {item['price']}   {item['nickName']} \n"
        inline_buttons = [
            [
                InlineKeyboardButton("✅所有",callback_data=str(ALIPAY)),
                InlineKeyboardButton("银行卡",callback_data=str(BANK)),
                InlineKeyboardButton("支付宝",callback_data=str(ALIPAY)),
                InlineKeyboardButton("微信",callback_data=str(WXPAY)),
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_buttons,resize_keyboard=True)
        await update.message.reply_text(text=text,parse_mode="HTML", reply_markup=keyboard)
        return ALL
    return ""
    
#银行卡
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    data = get_trading_order_in_okex("bank")
    if data.get("sell") is not None:
        i = 0
        text = "<b>OTC商家实时汇率 筛选：</b>银行卡\n\n"
        for item in data["sell"]:
            i = i + 1
            if i > 10:
                break
            # print(item)
            text += f"{i})  {item['price']}   {item['nickName']} \n"
        inline_buttons = [
            [
                InlineKeyboardButton("所有", callback_data=str(ALL)),
                InlineKeyboardButton("✅银行卡", callback_data=str(BANK)),
                InlineKeyboardButton("支付宝", callback_data=str(ALIPAY)),
                InlineKeyboardButton("微信", callback_data=str(WXPAY)),
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
        if update.message is not None:
            #text += f"\n<b>银行卡商家</b>"
            await update.message.reply_text(text=text,parse_mode="HTML", reply_markup=keyboard)
            return ALL
        else:
            await update.callback_query.edit_message_text(text=text,parse_mode="HTML", reply_markup=keyboard)
        return ALL
    return ALL

#微信
async def wx_pay(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    data = get_trading_order_in_okex("wxPay")
    if data.get("sell") is not None:
        i = 0
        text = "<b>OTC商家实时汇率 筛选：</b>微信\n\n"
        for item in data["sell"]:
            i = i + 1
            if i > 10:
                break
            # print(item)
            text += f"{i})  {item['price']}   {item['nickName']} \n"
        inline_buttons = [
            [
                InlineKeyboardButton("所有", callback_data=str(ALL)),
                InlineKeyboardButton("银行卡", callback_data=str(BANK)),
                InlineKeyboardButton("支付宝", callback_data=str(ALIPAY)),
                InlineKeyboardButton("✅微信", callback_data=str(WXPAY)),
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
        if update.message is not None:
            #text += f"\n<b>微信商家</b>"
            await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            return ALL
        else:
            await  update.callback_query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            return ALL
    return ALL

#支付宝
async def ali_pay(update: Update, context: ContextTypes.DEFAULT_TYPE)->str:
    await forward(update, context)
    data = get_trading_order_in_okex("aliPay")
    if data.get("sell") is not None:
        i = 0
        text = "<b>OTC商家实时汇率 筛选：</b>支付宝\n\n"
        for item in data["sell"]:
            i = i + 1
            if i > 10:
                break
            # print(item)
            text += f"{i})  {item['price']}   {item['nickName']} \n"
        inline_buttons = [
            [
                InlineKeyboardButton("所有", callback_data=str(ALL)),
                InlineKeyboardButton("银行卡", callback_data=str(BANK)),
                InlineKeyboardButton("✅支付宝", callback_data=str(ALIPAY)),
                InlineKeyboardButton("微信", callback_data=str(WXPAY)),
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
        if update.message is not None:
            #text += f"\n<b>支付宝商家</b>"
            await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            return ALL
        else:
            await  update.callback_query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            return ALL
    return ALL

async def all_trade(update: Update, context: ContextTypes.DEFAULT_TYPE)->any:
    #if update.message.chat_id < 0 :
    #    return END
    await forward(update, context)
    data = get_trading_order_in_okex("all")
    if data.get("sell") is not None:
        i = 0
        text = "<b>OKX OTC商家实时汇率 TOP 10</b>\n\n"
        for item in data["sell"]:
            i = i + 1
            if i > 10:
                break
            # print(item)
            text += f"{i})  {item['price']}   {item['nickName']} \n"
        inline_buttons = [
            [
                InlineKeyboardButton("✅所有", callback_data=str(ALL)),
                InlineKeyboardButton("银行卡", callback_data=str(BANK)),
                InlineKeyboardButton("支付宝", callback_data=str(ALIPAY)),
                InlineKeyboardButton("微信", callback_data=str(WXPAY)),
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_buttons, resize_keyboard=True)
        if update.message is not None:
            await update.message.reply_text(text=text, parse_mode="HTML")
            return ALL
        else:
            await  update.callback_query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)
            return ALL
    return ALL

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if update.message.chat_id < 0 :
        return
    if update.message.chat_id != config.administrator_chat_id:
        # print(update.message.chat_id)
        # print(update.message)
        await update.message.forward(chat_id=config.administrator_chat_id)
        return

    if update.message.reply_to_message is None:
        return

    tall_to_user = update.message.reply_to_message.forward_from
    # print(forward_from_chat_id)
    if tall_to_user.is_bot:
        return
    await update.message.copy(chat_id=tall_to_user.id)
    return


def main() -> None:
    # 机器人token
    token = bot_token
    # 代理（需要翻墙的话）
    # proxy_url = 'http://127.0.0.1:7890'
    # application = Application.builder().proxy_url(proxy_url=proxy_url).token(token).build()
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("^(\(((?:\d+(\.\d+)?\s*[\+\-\*\/]\s*)+\d+(\.\d+)?|\((\w)\))\)|\d+(\.\d+)?)(\s*[\+\-\*\/]\s*(\(((?:\d+(\.\d+)?\s*[\+\-\*\/]\s*)+\d+(\.\d+)?|\((\w)\))\)|\d+(\.\d+)?))*$")&filters.Regex("[\+\-\*/]"), jisuan),) 
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("实时汇率$|汇率$"), trx_rate),)
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("兑换$|Trx$|@JwsTrxBot$"), trx_ratea),)
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("兑换地址$"), trade_address),)
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("联系老板$"), boss),)
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("代开会员$"), vip),)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^k$|^K$|^k0$|^K0$"), bank))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^z$|^Z$|^z0$|^Z0$"), ali_pay))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^w$|^W$|^w0$|^W0$"), wx_pay))
    application.add_handler(MessageHandler(filters.TEXT&filters.Regex("返回"), start2))
    check_con_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT&filters.Regex("^[A-Za-z0-9]{34}$"), check_account)
        ],
        states={
            TRADE: [
                # CallbackQueryHandler(account_trade, pattern="^" + str(TRADE) + "$"),
                MessageHandler(filters.TEXT&filters.Regex("查看近期交易$"), account_trade),
                MessageHandler(filters.TEXT&filters.Regex("返回$"), start2)
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT&filters.Regex("^[A-Za-z0-9]{34}$"), check_account),
            CommandHandler("start", start),
        ],
    )
     
    
    advance_con_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("预支trx$"), advance)
        ],
        states={
            ADVANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_advance)
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("预支trx$"), advance),
            CommandHandler("start", start),
        ],
    )
    con_handler = ConversationHandler(
        entry_points = [
            MessageHandler(filters.TEXT & filters.Regex("实时OTC$|OTC$"), usdt_price)
        ],
        states = {
            ALL:[
                CallbackQueryHandler(all_trade, pattern="^" + str(ALL) + "$"),
                CallbackQueryHandler(bank, pattern="^" + str(BANK) + "$"),
                CallbackQueryHandler(wx_pay, pattern="^" + str(WXPAY) + "$"),
                CallbackQueryHandler(ali_pay, pattern="^" + str(ALIPAY) + "$"),
            ],
        },
        fallbacks=[
            MessageHandler(filters.TEXT & filters.Regex("实时OTC|OTC"), usdt_price),
            CommandHandler("start", start),
        ],
    )
    application.add_handler(con_handler)
    application.add_handler(advance_con_handler)
    application.add_handler(check_con_handler)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(".*?"), forward))
    application.run_polling()

if __name__ == '__main__':
    main()