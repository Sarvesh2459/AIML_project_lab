import json
from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
import requests


client = OpenAI(api_key="your_api_key")

app = Flask(__name__)

auth_array = ["", False]

with open('db.json') as json_file:
	db = json.load(json_file)

def commit():
    with open('db.json', 'w') as json_file:
        json.dump(db, json_file, indent=2)



@app.route('/')
def home():
    return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data=None)

@app.route('/classify', methods=['POST'])
def classify():
    if request.method == 'POST':
        text = request.form['text']
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": '''You are a banking chatbot. Give first line as intent of question: CHITCHAT, GET_BALANCE, TRANSFER_MONEY .     
            Second line will be response, if intent was TRANSFER_MONEY give ouptut ACNO:(Account Number in prompt), AMT:(Amount in prompt). If intent was
            CHITCHAT reply accordingly. If intent was GET_BALANCE give output ACNO:(Account Number in prompt)'''},
            {"role": "user", "content": text + ".My name is " + auth_array[0]}
        ]
        )

        gpt_response = completion.choices[0].message.content
        print(gpt_response)
        intent = gpt_response.split("\n")[0]
        intent = intent.strip()
        if intent == "CHITCHAT":
            return  render_template('index.html', text=text, prediction=intent,authorised=auth_array[1],name=auth_array[0], data=gpt_response.split("\n")[1])
        elif intent == "TRANSFER_MONEY":
            to_acc, amt = gpt_response.split("\n")[1].split(',')
            to_acc = to_acc.split(':')[1]
            amt = amt.split(':')[1]
            return render_template('transfer.html',name=auth_array[0], data=to_acc, amt=amt)
        elif intent == "GET_BALANCE":
            acc = gpt_response.split("\n")[1].split(":")[1].strip()
            response = requests.get("http://localhost:5000/get_details/"+acc)
            if response.status_code == 200:
                det = response.json()
                if det["name"] != "":
                    return render_template('index.html', text=text, prediction=intent,authorised=auth_array[1],name=auth_array[0], data="Name is " + det["name"] + " .Balance is "+ det['balance'])
                else:
                    return render_template('index.html', text=text, prediction=intent,authorised=auth_array[1],name=auth_array[0], data="No such user found")
        else:
            return render_template('index.html', text=text, prediction=None, authorised=auth_array[1],name=auth_array[0],data=gpt_response)

@app.route('/get_user', methods=['POST'])
def get_user():
    name = request.form['name']
    accno = request.form['accno']
    auth = request.form['auth']
    for users in db:
        if users['name'] == name and users["acc_no"] == accno:
            if users["auth_code"] == auth:
                auth_array[0] = name
                auth_array[1] = True
                return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Auth Successful")
            else:
                return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Auth Failed")
    
    return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Auth Failed")
     
@app.route('/transfer_money', methods=['POST'])
def transfer_money():
    if auth_array[1] == True:
        name = request.form['name']
        accno = request.form['data']
        amt = request.form['amt']
        print(name, accno, amt)
        response = requests.get("http://localhost:5000/user_search/"+name)
        
        if response.status_code == 200:
            det = response.json()
            if det['name'] != "" and int(det['balance']) >= int(amt):
                for users in db:
                    if users['name'] == name:
                        users['balance'] = str(int(users['balance']) - int(amt))
                        for user2 in db:
                            if user2['acc_no'] == accno:
                                user2['balance'] = str(int(user2['balance']) + int(amt))
                                commit()     
                                return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Transfer Successful")      
        return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Transfer Failed")
    else:
        return render_template('index.html', prediction=None, authorised=auth_array[1],name=auth_array[0], data="Not Authorised")


@app.route('/user_search/<name>', methods=['get'])
def user_name(name):
    for users in db:
        if users['name'] == name:
            return {"name": users['name'], "balance": users['balance'], "acc_no": users['acc_no']}
    return {"name": ""}
            
@app.route('/get_details/<acc>', methods=['get'])
def get_details(acc):
    for users in db:
        if users['acc_no'] == acc:
            return {"name": users['name'], "balance": users['balance'], "acc_no": users['acc_no']}
    return {"name": ""}

if __name__ == '__main__':
    app.run(debug=True)
