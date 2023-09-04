import os
from flask import Flask, render_template, request, redirect, jsonify, redirect, url_for, session
from zenora import APIClient
from flask_cors import *
import requests
import asyncio
import random
import datetime
import pytz
import time

from pymongo import MongoClient
import pymongo
import certifi
from utility.config import config
from cogs.function_in import function_in
import json

app = Flask(__name__, static_folder='templates', static_url_path='/static')
secret_key = os.urandom(24)
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 900
CORS(app, supports_credentials=True)
oauth_url = "discord連結"
callback_url = "https://rbctw.xyz/oauth/callback"
client = APIClient(os.environ.get("DISCORD_TOKEN"), client_secret=os.environ.get("CLIENT_SECRET"))

@app.route('/ping', methods=['POST', 'OPTIONS', 'GET', 'HEAD'])
def ping():
    return {'message': 'OK'}

@app.route('/discord')
async def discord():
    return redirect("https://discord.gg/rbc-tw", code=302)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/oauth/callback')
async def callback():
    code = request.args['code']
    access_token = client.oauth.get_access_token(code, callback_url).access_token
    session['token'] = access_token
    bearer_client = APIClient(session.get("token"), bearer=True)
    current_user = bearer_client.users.get_current_user()
    session['username'] = current_user.username
    user_id = int(f"{current_user.id}")
    session["user_id"] = user_id
    cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
    db = cluster["web_admin"]
    collection = db["all"]
    if collection.count_documents({"_id": user_id}) == 0:
        session["admin_per"] = False
    else:
        for user_info in collection.find({"_id": user_id}):
            admin_class = user_info["admin_class"]
        session["admin_per"] = True
        session["admin_class"] = admin_class
    print(f"{current_user.avatar_url}")

    if f"{current_user.avatar_url}" == "None":
        session["avatar_url"] = "https://i.imgur.com/CzdcDME.png"
    else:
        session["avatar_url"] = current_user.avatar_url
    return redirect('/admin_index')

@app.route('/check_level', methods=['POST'])
async def check_level():
    if request.method == 'POST':
        cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
        db = cluster["discordbot"]
        collection = db["Level"]
        responselist = []
        
        a = 0
        for 等級 in (
            collection.find({})
            .sort("總經驗值", pymongo.DESCENDING)
            .limit(10)
        ):
            a += 1
            user_id = 等級["_id"]
            level = 等級["等級"]
            exp = 等級["經驗值"]
            total_exp = 等級["總經驗值"]
            guild_id = config.guild
            headers = {
                'Authorization': f'Bot {os.environ.get("DISCORD_TOKEN")}'
            }
            url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}'
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                global_name = user_data['user']["global_name"]
                nick = user_data['nick']
                if not nick:
                    nick = "無"
                usernewid = user_data['user']["username"]
                responselist.append({"id": user_id, "global_name": global_name,"nick": nick, "usernewid": usernewid, "level": level, "exp": exp, "total_exp": total_exp})
            else:
                url = f'https://discord.com/api/v9/users/{user_id}'
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    global_name = user_data["global_name"]
                    usernewid = user_data["username"]
                    responselist.append({"id": user_id, "global_name": global_name,"nick": "機器人無法獲取", "usernewid": usernewid, "level": level, "exp": exp, "total_exp": total_exp})
                    continue
                responselist.append({"id": "該用戶無法被機器人取得", "global_name": "X","nick": "X", "usernewid": "X", "level": "X", "exp": "X", "total_exp": "X"})

        response = app.response_class(
            response=json.dumps(responselist),
            status=200,
            mimetype='application/json'
        )
        return response

@app.route('/discord_id_check', methods=['POST'])
async def discord_id_check():
    if request.method == 'POST':
        data = request.get_json()
        discord_id = data.get('discord_id')
        headers = {
            'Authorization': f'Bot {os.environ.get("DISCORD_TOKEN")}'
        }
        url = f'https://discord.com/api/v9/guilds/{config.guild}/members/{discord_id}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            global_name = user_data['user']["global_name"]
            usernewid = user_data['user']["username"]
            avatar = user_data['user']["avatar"]
        else:
            url = f'https://discord.com/api/v9/users/{discord_id}'
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                global_name = user_data["global_name"]
                usernewid = user_data["username"]
                avatar = user_data["avatar"]
        
        response_data = {
            'global_name': global_name,
            "usernewid": usernewid,
            "avatar": avatar
        }
        response = jsonify(response_data)
        return response

@app.route('/appeal_accept', methods=["POST"])
async def appeal_accept():
    data = request.get_json()
    punid = data.get('punid')
    accept = data.get('appeal_accept')
    cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
    db = cluster["punish"]
    collection = db["all"]
    collection1 = db["appeal"]
    for pun_info in collection.find({"_id": punid}):
        canappeal = pun_info['canappeal']
        if canappeal != "上訴審核中":
            response_data = {
                'message': 'no',
            }
        else:
            if accept == "yes":
                collection1.delete_one({"_id": punid})
                await function_in.collection_update_one(collection, punid, "canappeal", "上訴審核成功, 懲罰撤銷")
            else:
                collection1.delete_one({"_id": punid})
                await function_in.collection_update_one(collection, punid, "canappeal", "上訴審核駁回, 懲罰不變")
            response_data = {
                'message': 'yes'
            }
    response = jsonify(response_data)
    return response

@app.route('/see_appeal_config', methods=["POST"])
async def see_appeal_config():
    data = request.get_json()
    punid = data.get('punid')
    cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
    db = cluster["punish"]
    collection = db["all"]
    collection1 = db["appeal"]
    for pun_info in collection.find({"_id": punid}):
        canappeal = pun_info['canappeal']
    for pun_info in collection1.find({"_id": punid}):
        reason1 = pun_info["reason1"]
        reason2 = pun_info["reason2"]
        reason3 = pun_info["reason3"]
    if canappeal == "上訴審核中":
        response = {
            'canappeal': True,
            'reason1': reason1,
            'reason2': reason2,
            'reason3': reason3
        }
    else:
        response = {
            'canappeal': False
        }
    response = jsonify(response)
    return response

@app.route('/see_all_appeal', methods=["POST"])
async def see_all_appeal():
    cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
    db = cluster["punish"]
    collection = db["all"]
    if collection.count_documents({}) == 0:
        response_data = {
        'message': '無',
        }
        response = jsonify(response_data)
    else:
        response_data = []
        for puninfo in collection.find():
            punid = puninfo["_id"]
            admin_id = puninfo["admin"]
            user_id = puninfo["member"]
            reason = puninfo["reason"]
            punish_type = puninfo["punish_type"]
            start_time = puninfo["start_time"]
            pun_time = puninfo["time"]
            if punish_type == "禁言":
                punish = f"禁言 {pun_time}"
            else:
                if pun_time == "永久":
                    punish = "永久停權"
                else:
                    punish = f"停權 {pun_time}"
            canappeal = puninfo["canappeal"]
            if canappeal != "上訴審核中":
                continue
            response_data.append({"punid": punid, "admin_id": admin_id, "user_id": user_id, "reason": reason, "punish": punish, "start_time": start_time, "canappeal": canappeal})
        if response_data == []:
            response_data = {
            'message': '無',
            }
            response = jsonify(response_data)
        else:
            response = jsonify({"data": response_data})
    return response

@app.route('/see_appeal', methods=['POST'])
async def see_appeal():
    if request.method == 'POST':
        data = request.get_json()
        discord_id = data.get('discord_id')
        cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
        db = cluster["punish"]
        collection = db["all"]
        if collection.count_documents({"member": int(discord_id)}) == 0:
            response_data = {
            'message': '無',
            }
            response = jsonify(response_data)
        else:
            response_data = []
            for puninfo in collection.find({"member": int(discord_id)}):
                punid = puninfo["_id"]
                admin_id = puninfo["admin"]
                reason = puninfo["reason"]
                punish_type = puninfo["punish_type"]
                start_time = puninfo["start_time"]
                pun_time = puninfo["time"]
                if punish_type == "禁言":
                    punish = f"禁言 {pun_time}"
                else:
                    if pun_time == "永久":
                        punish = "永久停權"
                    else:
                        punish = f"停權 {pun_time}"
                canappeal = puninfo["canappeal"]
                response_data.append({"punid": punid, "admin_id": admin_id, "reason": reason, "punish": punish, "start_time": start_time, "canappeal": canappeal})
                response = jsonify({"data": response_data})
        return response

@app.route('/appeal_upload', methods=['POST'])
async def appeal_upload():
    data = request.get_json()
    punid = data.get('punid')
    reason1 = data.get('reason1')
    reason2 = data.get('reason2')
    reason3 = data.get('reason3')
    cluster = MongoClient(config.mongo_url, tlsCAFile=certifi.where())
    db = cluster["punish"]
    collection = db["all"]
    collection1 = db["appeal"]
    for pun_info in collection.find({"_id": punid}):
        canappeal = pun_info['canappeal']
    if canappeal == "可上訴":
        append = {
            "_id": punid,
            "reason1": reason1,
            "reason2": reason2,
            "reason3": reason3,
        }
        await function_in.collection_update_one(collection, punid, "canappeal", "上訴審核中")
        collection1.insert_one(append)
        response = {
            "upload": "ok"
        }
    else:
        response = {
            "upload": "no"
        }
    response = jsonify(response)
    return response

@app.route('/donate_done', methods=['POST'])
def donate_done():
    data = request.get_json()
    print('done:' + str(data))

@app.route('/donate_test')
def donate_test():
    if request.method == "GET":
        now_time = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime('%Y-%m-%d %H:%M:%S')
        timeString = now_time
        struct_time = time.strptime(timeString, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(struct_time))
        headers = {
            'MerchantID': '2000132',
            'TimeStamp': f'{time_stamp}',
            'LoginBackUrl': 'https://rbctw.xyz/donate_test'
        }
        url = 'https://login-stage.opay.tw/OpenID/Login'
        response = requests.post(url, headers=headers)
        return f"{response}"
    if request.method == "POST":
        data = request.get_json()
        print(data)

@app.route("/logout")
async def logout():
    session.clear()
    return redirect("https://rbctw.xyz")
    
@app.route('/')
def index():
    if "token" in session:
        return render_template('index.html', session=session)
    else:
        return render_template('index.html', session=None)
    
@app.route('/donate')
def donate():
    if "token" in session:
        return render_template('donate.html', session=session)
    else:
        return render_template('donate.html', session=None)

@app.route('/classlevel')
def classlevel():
    if "token" in session:
        return render_template('classlevel.html', session=session)
    else:
        return render_template('classlevel.html', session=None)

@app.route('/finish')
def finish():
    if "token" in session:
        return render_template('finish.html', session=session)
    else:
        return render_template('finish.html', session=None)

@app.route('/main_appeal')
def main_appeal():
    if "token" in session:
        return render_template('main_appeal.html', session=session)
    else:
        return render_template('main_appeal.html', session=None)

@app.route('/sendappealmessage')
def sendappealmessage():
    if "token" in session:
        return render_template('sendappealmessage.html', session=session)
    else:
        return render_template('sendappealmessage.html', session=None)

@app.route('/senddiscordid')
def senddiscordid():
    if "token" in session:
        return render_template('senddiscordid.html', session=session)
    else:
        return render_template('senddiscordid.html', session=None)

@app.route('/sendpunishid')
def sendpunishid():
    if "token" in session:
        return render_template('sendpunishid.html', session=session)
    else:
        return render_template('sendpunishid.html', session=None)

@app.route("/login")
def login():
    if "token" in session:
        return redirect("/admin_index")
    else:
        return redirect(oauth_url)

@app.route("/admin_index")
def admin_index():
    if "token" in session:
        return render_template("admin_index.html", session=session)
    else:
        return redirect("/login")

@app.route("/manage_appeal")
def manage_appeal():
    if "token" in session:
        return render_template("manage_appeal.html", session=session)
    else:
        return redirect("/login")

@app.route("/manage_appealmessage")
def manage_appealmessage():
    if "token" in session:
        return render_template("manage_appealmessage.html", session=session)
    else:
        return redirect("/login")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
