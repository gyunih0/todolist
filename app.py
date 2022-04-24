from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify
import certifi
from datetime import datetime


ca = certifi.where()
app = Flask(__name__)

client = MongoClient(
    'mongodb+srv://test:sparta@cluster0.7y6m3.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

# 오늘 날짜 아닌 데이터 삭제하기
# 1. 오늘 잘짜 인가?
# 2. tag 가 저장되어 있나?
# 3. 완료가 되어있나?


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
        'tag': []
    }
    db.todo.insert_one(doc)

    return jsonify({'msg': '등록완료', 'num': count})


@app.route("/todo/done", methods=["POST"])
def todo_done():
    num_receive = request.form['num_give']
    date_receive = request.form['date_give']
    db.todo.update_one({'num': int(num_receive)}, {'$set': {'done': 1}})

    todo_list = list(db.todo.find({'date': date_receive}, {'_id': False}))
    tag_list = list(db.todo_tags.find({'num': int(num_receive)}, {'_id': False}))

    for todo in todo_list:
        # 테그 저장 부분
        if todo['tag']:  # todo에 tag가 저장되있다면

            if len(tag_list) != 0:
                print("기존 tag 수정")
                for tags in tag_list:  # 그 todo의 num가 todo_tags 에 있다면 tag 수정

                    if todo['num'] == tags['num']:
                        db.todo_tags.update_one({'num': todo['num']}, {'$set': {'tag': todo['tag']}})
                        print(tags['num'], "updated")
            else:  # 신규 저장 이라면
                print("신규 tag")
                doc = {
                    'date': todo['date'],
                    'todo': todo['todo'],
                    'num': todo['num'],
                    'tag': todo['tag'],
                    'comment': todo['comment']
                }
                print(doc)
                db.todo_tags.insert_one(doc)
                print('new tag updated')

    # percentage 처리 부분
    done_count = 0
    total = len(todo_list)
    for todo in todo_list:
        if todo['done'] == 1:
            done_count += 1
    percentage = done_count / total
    percent_level = 0
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

    # split tags & append in tag_list
    tag_words = tag_receive.replace('#', ',')
    words_list = tag_words.split(',')
    tag_list = []

    for i in range(len(words_list)):  # 공백 문자 제거, 중복 제거
        words_list[i] = words_list[i].strip()
        if words_list[i] != '' and words_list[i] not in tag_list:
            tag_list.append(words_list[i])

    db.todo.update_one({'num': int(num_receive)}, {'$set': {'comment': comment_receive, 'tag': tag_list}})
    print(tag_list, 'saved in todo #num{}'.format(num_receive))
    return jsonify({'msg': 'comment, tag 완료!'})


@app.route("/todo", methods=["GET"])
def todo_get():
    todo_list = list(db.todo.find({}, {'_id': False}))

    # 지난 todolist 삭제하기
    today_date = datetime.today().strftime('%m/%d/%Y')
    # print(today_date)
    for todo in todo_list:
        # 지난 date / 완료 x / tag 입력 x 인 것 들을 삭제
        if todo['date'] != today_date:
            print(todo['num'], "deleted")
            db.todo.delete_one({'num': int(todo['num'])})

    return jsonify({'todos': todo_list})


@app.route("/todo/delete", methods=["POST"])
def todo_delete():
    num_receive = request.form['num_give']
    db.todo.delete_one({'num': int(num_receive)})

    return jsonify({'msg': '삭제 완료!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)