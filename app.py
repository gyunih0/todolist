from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify
import certifi
ca = certifi.where()
app = Flask(__name__)

client = MongoClient(
    'mongodb+srv://test:sparta@cluster0.7y6m3.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta


@app.route('/')
def home():

    return render_template('index.html')


@app.route("/todo", methods=["POST"])
def todo_post():
    date_receive = request.form['date_give']
    todo_receive = request.form['todo_give']
    print(todo_receive, date_receive)

    todo_list = list(db.todo.find({}, {'_id': False}))

    num_list = []  # num 속성 중복 오류를 막기 위함
    for todo in todo_list:
        num_list.append(todo['num'])

    count = len(todo_list) + 1
    while count in num_list:
        count += 1

    print(num_list, count)

    doc = {
        'date': date_receive,
        'num': count,
        'todo': todo_receive,
        'done': 0
    }
    db.todo.insert_one(doc)

    return jsonify({'msg': '등록완료', 'num': count})


@app.route("/todo/done", methods=["POST"])
def todo_done():
    num_receive = request.form['num_give']
    db.todo.update_one({'num': int(num_receive)}, {'$set': {'done': 1}})
    return jsonify({'msg': 'done 완료!'})


@app.route("/todo", methods=["GET"])
def todo_get():
    todo_list = list(db.todo.find({}, {'_id': False}))
    return jsonify({'todos': todo_list})


@app.route("/todo/delete", methods=["POST"])
def todo_delete():
    num_receive = request.form['num_give']
    db.todo.delete_one({'num': int(num_receive)})

    return jsonify({'msg': '삭제 완료!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)