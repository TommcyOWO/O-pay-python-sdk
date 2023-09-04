import requests as rq

url = "https://payment.opay.tw/Cashier/AioCheckOut/V5"
test_url = "https://payment-stage.opay.tw/Cashier/AioCheckOut/V5"

# POST 
#建立訂單 必要
MerchantID = str(10)
MerchantTradeNo = str(20)
MerchantTradeDate = str(20)
TotalAmount = int
TradeDesc = str(200)
ItemName = str(200)
ReturnURL = str(200)
ChoosePayment = str(20)
PaymentType = str(20) #請固定填入"aio"。
CheckMacValue = str("max")

#==========================================#
import hashlib
import urllib.parse

# 特殊字元置換
def replace_char(value):
    search_list = ['%2d', '%5f', '%2e', '%21', '%2a', '%2A', '%28', '%29']
    replace_list = ['-', '_', '.', '!', '*', '*', '(', ')']
    for search, replace in zip(search_list, replace_list):
        value = value.replace(search, replace)
    return value

# 產生檢查碼
def get_mac_value(hash_key, hash_iv, form_dict):
    encode_str = f"HashKey={hash_key}"
    for key, value in form_dict.items():
        encode_str += f"&{key}={value}"
    encode_str += f"&HashIV={hash_iv}"
    encode_str = urllib.parse.quote(encode_str.lower(), safe='')
    encode_str = replace_char(encode_str)
    return hashlib.md5(encode_str.encode()).hexdigest()

# 歐富寶超商付費訂單資訊
order_data = {
    "MerchantID": "YourMerchantID",  # 商店代號
    "MerchantTradeNo": "YourTradeNo",  # 訂單編號
    "MerchantTradeDate": "2023/09/04 14:30:00",  # 訂單日期時間
    "PaymentType": "CVS",  # 付款方式（超商代碼繳費）
    "TotalAmount": "100",  # 交易金額
    "TradeDesc": "YourTradeDesc",  # 交易描述
    "ItemName": "YourItemName",  # 商品名稱
    "ReturnURL": "http://www.yourwebsite.com/return",  # 交易完成後返回的網址
    "ChoosePayment": "CVS",  # 選擇超商付款
    "ClientBackURL": "http://www.yourwebsite.com",  # 返回商店的網址
}

# 計算檢查碼
check_mac_value = get_mac_value("YourHashKey", "YourHashIV", order_data)

# 將檢查碼添加到訂單資料
order_data["CheckMacValue"] = check_mac_value

# 發送 POST 請求創建訂單
async def create_order():
    response = rq.post(test_url, data=order_data)
    if response.status_code == 200:
        print("訂單建立成功，請前往超商繳費。")
        return response.json
    else:
        print("訂單建立失敗。")
        return None