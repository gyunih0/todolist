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
        'done': 0,
        'comment': '',
        'tag': ''
    }
    db.todo.insert_one(doc)

    return jsonify({'msg': '등록완료', 'num': count})


@app.route("/todo/done", methods=["POST"])
# 당일 전체 할일 갯수 중에 완료된거 갯수 업데이트 해서 1~5단계로 percentage 저장/업데이트 해야됨, ex){type: percentage, percentage: 1~5}
def todo_done():
    num_receive = request.form['num_give']
    date_receive = request.form['date_give']
    db.todo.update_one({'num': int(num_receive)}, {'$set': {'done': 1}})

    todo_list = list(db.todo.find({'date': date_receive}, {'_id': False}))
    done_count = 0
    percent_level = 0
    total = len(todo_list)
    for todo in todo_list:
        if todo['done'] == 1:
            done_count += 1
    percentage = done_count / total

    if percentage == 0:
        percent_level = 0
    elif percentage <= 0.25:
        percent_level = 1
    elif percentage <= 0.5:
        percent_level = 2
    elif percentage <= 0.75:
        percent_level = 3
    elif percentage < 1:
        percent_level = 4
    else:
        percent_level = 5

    print(done_count, percentage, 'percent_level = {}'.format(percent_level))

    done_percentage = list(db.todo_percent.find({'date': date_receive}, {'_id': False}))
    if len(done_percentage) == 0:
        print('No date')
        doc = {
            'date': date_receive,
            'percent_level': percent_level
        }
        db.todo_percent.insert_one(doc)
    else:
        db.todo_percent.update_one({'date': date_receive}, {'$set': {'percent_level': percent_level}})

    return jsonify({'msg': 'done 완료!'})


@app.route("/todo/comment", methods=["POST"])
def todo_comment():
    num_receive = request.form['num_give']
    comment_receive = request.form['comment_give']
    tag_receive = request.form['tag_give']

    db.todo.update_one({'num': int(num_receive)}, {'$set': {'comment': comment_receive, 'tag': tag_receive}})
    return jsonify({'msg': 'comment, tag 완료!'})


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