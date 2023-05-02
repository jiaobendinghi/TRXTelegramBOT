import requests,json,time
from tronpy.keys import is_base58check_address
from .bot_config import commission,tronscan_api,usdt_address
# 获取trx当前汇率
def get_trx_rate_bian() -> float:
    url = "https://api.binance.com/api/v3/ticker/price?symbol=TRXUSDT"

    headers = {"Accept": "application/json"}

    rsp = requests.request("GET", url, headers=headers)
    res = json.loads(rsp.text)
    c = commission
    if res.get("price") is not None:
        price = float(res["price"])
        r = 1 / price
        if r - c < 0:
            c = 1
        return r - c
    return 14.00

def get_trx_rate() -> float:
    url = "https://www.okx.com/api/v5/market/index-components?index=TRX-USDT"
    headers = {"Accept": "application/json"}

    rsp = requests.request("GET", url, headers=headers)
    res = json.loads(rsp.text)
    c = commission
    if res.get("data") is not None:
        price = float(res["data"]["last"])
        r = 1 / price
        if r - c < 0:
            c = 1
        return r - c
    return 14.00

# 校验地址
def check_address(address) -> bool:
    if is_base58check_address(address):
        return True
    return False

#查ok交易所
def get_trading_order_in_okex(payment_method="all")->any:
    api = "https://www.okx.com/v3/c2c/tradingOrders/books"
    t = int(round(time.time() * 1000))
    url = api+"?t="+ str(t) +"&quoteCurrency=cny&baseCurrency=usdt" \
                           f"&side=sell&paymentMethod={payment_method}&userType=all&receivingAds=false"

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    rsp = requests.request("GET", url, headers=headers)
    res = json.loads(rsp.text)
    if res.get("data") is not None:
        return res["data"]
    return None

def account_info(address:str):
    url = tronscan_api+f"api/accountv2?address={address}"
    headers = {"Accept": "application/json"}

    rsp = requests.request("GET", url, headers=headers)
    res = json.loads(rsp.text)
    info = {"trx":0,"usdt":0,"transactions_out":0,"transactions_in":0,"transactions":0,
            "date_created":0,"latest_operation_time":0,
            "energy_remaining":0,"energy_used":0,"delegate_frozen_for_energy":0,
            "free_net_limit":0,"free_net_remaining":0,"address":address}
    if res.get("activated") is not None:
        info["trx"] = res["balance"] / 10**6
        for item in res["withPriceTokens"]:
            if item["tokenId"] == usdt_address:
                info["usdt"] = int(item["balance"]) / 10**6
        info["transactions_out"] = res["transactions_out"]
        info["transactions_in"] = res["transactions_in"]
        info["transactions"] = res["transactions"]
        info["date_created"] = res["date_created"]
        info["latest_operation_time"] = res["latest_operation_time"]
        info["energy_remaining"] = res["bandwidth"]["energyRemaining"]
        info["energy_limit"] = res["bandwidth"]["energyLimit"]
        info["free_net_limit"] = res["bandwidth"]["freeNetLimit"]
        info["free_net_remaining"] = res["bandwidth"]["freeNetRemaining"]
        info["delegate_frozen_for_energy"] = res["delegateFrozenForEnergy"]
        return info
    return info

def account_token_trc20_usdt(address):
    url = tronscan_api + f"api/token_trc20/transfers?limit=20&start=0&sort=-timestamp&" \
                         f"count=true&tokens={usdt_address}&filterTokenValue=1&relatedAddress={address}"
    headers = {"Accept": "application/json"}
    rsp = requests.request("GET", url, headers=headers)
    res = json.loads(rsp.text)
    record = {"in":[],"out":[]}
    if res.get("token_transfers") is not None:
        for item in res["token_transfers"]:
            if item["from_address"] == address:
                rec = {"block_ts":item["block_ts"],"amount":int(item["quant"])/10**6,"transaction_id":item["transaction_id"]}
                record["out"].append(rec)
            else:
                rec = {"block_ts": item["block_ts"], "amount": int(item["quant"]) / 10 ** 6, "transaction_id": item["transaction_id"]}
                record["in"].append(rec)

    return record