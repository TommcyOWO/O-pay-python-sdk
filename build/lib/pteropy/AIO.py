import hashlib
import urllib.parse

class AIO:
    def __init__(self,hash_key,hash_iv,form_dict):
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.form_dict = form_dict
        
    # 產生檢查碼
    def get_mac_value(self):
        encode_str = f"HashKey={self.hash_key}"
        for key, value in self.form_dict.items():
            encode_str += f"&{key}={value}"
        encode_str += f"&HashIV={self.hash_iv}"
        encode_str = urllib.parse.quote(encode_str.lower(), safe='')
        encode_str = self.replace_char(encode_str)
        return hashlib.md5(encode_str.encode()).hexdigest()
    
    # 特殊字元置換
    def replace_char(self, value):
        search_list = ['%2d', '%5f', '%2e', '%21', '%2a', '%2A', '%28', '%29']
        replace_list = ['-', '_', '.', '!', '*', '*', '(', ')']
        for search, replace in zip(search_list, replace_list):
            value = value.replace(search, replace)
        return value
    
    # 仿自然排序法
    def merchant_sort(self,a, b):
        return self.strcasecmp(a, b)

    # 仿 strcasecmp 函式
    def strcasecmp(self,a, b):
        return (a > b) - (a < b)