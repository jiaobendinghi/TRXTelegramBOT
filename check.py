import func.bot_config as config
# 机器人token 在telegram的botFather上设置 （敏感信息）
bot_token = config.bot_token

# 波场API地址 在 https://www.trongrid.io/ 上申请（敏感信息）
trongrid_api_key = config.trongrid_api_key

# 钱包公钥
bot_address = config.bot_address
#转账成功后通知的群id
group_id = config.group_id

# 钱包私钥 （敏感信息）
pri_key = config.pri_key
trongrid_api = config.trongrid_api
uri = trongrid_api + bot_address + f"/transactions/trc20?only_confirmed=true&only_to=true&&limit=50&min_timestamp="

#汇率抽成 % 小于100  例如：抽5%则填5
commission = config.commission

import json,time,requests
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from func.mysql import conn_db
from func.mysql_func import insert_order,check_transaction_id,need_advance
from func.func import get_trx_rate
from apscheduler.schedulers.blocking import BlockingScheduler


def send(message:str):
    # 设置请求参数
    data = {
        "chat_id": group_id,
        "text": message,
        "parse_mode":"HTML",
    }
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    requests.post(api_url, data=data)  # ,proxies=proxies)
    # 获取响应内容


def task_get_order():
    headers = {"accept": "application/json"}
    timestamp = int(time.time() - 60*50) * 1000
    url = uri + f"{timestamp}"
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    if data['success']:
        trx_rate = get_trx_rate()
        for d in data["data"]:
            if d["token_info"]["address"] == config.usdt_address and d["type"] == "Transfer":
                if config.min_usdt_amount <= int(d["value"])/1_000_000 <= config.max_usdt_amount:
                    order = dict()
                    usdt_amount = int(d["value"])/1_000_000
                    transaction_id = d["transaction_id"]
                    if check_transaction_id(transaction_id):
                        continue

                    trx_amount = usdt_amount * trx_rate
                    pre_trx = float(config.pre_pay_trx)

                    # 查预支
                    if need_advance(d["from"]):
                        order["advance_trx"] = pre_trx
                        order["trx_amount"] = round((trx_amount - config.pre_pay_trx),3)
                    else:
                        order["advance_trx"] = 0
                        order["trx_amount"] = round(trx_amount,3)

                    order["address"] = d["from"]
                    order["usdt_amount"] = round(usdt_amount,3)
                    # order["trx_amount"] = round(usdt_amount * trx_rate,3)
                    order["transaction_id"] = transaction_id
                    order["trx_rate"] = trx_rate
                    insert_order(order)

def task_transfer_trx():
    sql = f"select * from `bot_2500`.`order` where `status`=0"
    db = conn_db()
    cursor = db.cursor()
    cursor.execute(sql)
    orders = cursor.fetchall()
    # print(bool(orders))
    if bool(orders):
        if config.is_testnet:
            client = Tron(network="shasta")
        else:
            provider = HTTPProvider(api_key=[config.trongrid_api_key])
            client = Tron(provider)
        # provider = HTTPProvider(api_key=trongrid_api_key)
        # client = Tron(provider)
        private_key = PrivateKey(bytes.fromhex(pri_key))
        for order in orders:
            transfer_amount = int(order['trx_amount'] * 1_000_000)
            txn = (
                client.trx.transfer(config.bot_address, str(order['address']), transfer_amount)
                .build()
                .sign(private_key)
            )
            tx_id = txn.txid
            res = txn.broadcast().wait()
            if res.get('id') is not None:
                sql = f"UPDATE `bot_2500`.`order` SET `status` = 1 ,`tx_id`='{tx_id}'WHERE `id` = {order['id']} "
                try:
                    cursor.execute(sql)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(e)
                # 获得当前时间时间戳
                now = int(time.time())
                t = time.localtime(now)
                other_style_time = time.strftime("%Y-%m-%d %H:%M:%S", t)
                text = (
                    f"<b>新交易💸兑换 {order['trx_amount']} TRX</b>\n\n"
                    f"兑换金额：{order['usdt_amount']} USDT\n"
                    f"预支金额：{order['advance_trx']}\n"
                    f"兑换时间：{order['create_at']}\n"
                    f"兑换地址：{order['address'][0:5]}...{order['address'][-5:]}\n"
                    f"成交时间：{other_style_time}\n"
                )
                time.sleep(0.2)
                send(message=text)

    cursor.close()
    db.close()

# def go_task():
#     task_get_order()
#     task_transfer_trx()

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(task_get_order, 'interval', seconds=8)
    scheduler.add_job(task_transfer_trx, 'interval', seconds=7)
    # scheduler.add_job(go_task, 'interval', seconds=7)
    scheduler.start()