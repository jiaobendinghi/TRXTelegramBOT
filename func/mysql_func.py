import random
import time
from .bot_config import pre_pay_trx
from .mysql import conn_db
#查看地址订单交易情况
def check_address_order(address:str)->bool:
    sql = f"select count(*) as count from `bot_2500`.`order` where address = '{address}' and `status` = 1"
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res['count'] > 0:
        return True
    return False

def select_last_advance(address:str):
    sql = f"select * from `order` where address = '{address}' and type = 1 order by `id` desc limit 1"
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res

#查看usdt兑换总额
def sum_order_usdt_amount(address:str,begin=0):
    if begin == 0:
        sql = f"select COALESCE(sum(`usdt_amount`),0) as `sum` from `order` where address = '{address}'"
    else:
        sql = f"select COALESCE(sum(`usdt_amount`),0) as `sum` from `order` where address = '{address}' and `id` >{begin}"
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res

# 生成预支订单
def create_advance_order(address):
    random_num = time.time() + random.random()
    sql = f"INSERT INTO `order` ( `address`, `transaction_id`, `trx_amount`,`type`) " \
          f"VALUES ('{address}', '{random_num}', {pre_pay_trx},1)"
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

# 生成订单
def insert_order(order: dict):
    conn = conn_db()
    cursor = conn.cursor()
    sql = f"INSERT INTO `bot_2500`.`order` (`address`, `transaction_id`,`advance_trx`, `trx_amount`, `usdt_amount`,`trx_rate`) " \
          f"VALUES ('{order['address']}', '{order['transaction_id']}', {order['advance_trx']},{order['trx_amount']}, {order['usdt_amount']},{order['trx_rate']})"
    # print(sql)
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

# 查询transaction_id查看该订单是否存在 存在返回True 否则False
def check_transaction_id(transaction_id):
    db = conn_db()
    sql = f"select `id` from `bot_2500`.`order` where `transaction_id` = '{transaction_id}'"
    with db.cursor() as cursor:
        cursor.execute(sql)
        res = cursor.fetchall()
    if bool(res):
        return True
    else:
        return False

# 是否要扣预支的trx True 要扣 False 不扣
def need_advance(address)->bool:
    sql = f"select * from `order` where address = '{address}' order by `id` desc limit 1"
    conn = conn_db()
    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res is not None:
        if res["type"] == 1:
            return True
    return False