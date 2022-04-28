'''
2022.04.28
>> db.todo_percent 의 자료형 변경
>> todo_done, todo_post, todo_delete 에 대해서 db.todo_percent 업데이트 되도록 수정.
'''

'''

완료한 상태 (todo_percent & todo_tags 업데이트된 상태) 에서는
삭제 버튼(function delete_one())눌렀을 때 해당하는 todo의 todo_tags의 데이터도 삭제 할 것인가?

num 중복 적용 (해결)
'''

from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify
import certifi
from datetime import datetime


ca = certifi.where()
app = Flask(__name__)

client = MongoClient(
    'mongodb+srv://test:sparta@cluster0.7y6m3.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta


def return_percent_level(done, total):
    percent_level = 0
    if done == 0 and total == 0:
        percentage = 0
    else:
        percentage = done / total

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

    return percent_level


@app.route('/')
def home():

    return render_template('index.html')


@app.route("/todo", methods=["POST"])
def todo_post():
    date_receive = request.form['date_give']
    todo_receive = request.form['todo_give']

    tag_list = list(db.todo_tags.find({}, {'_id': False}))
    todo_list = list(db.todo.find({}, {'_id': False}))
    percent_list = list(db.todo_percent.find({'date': date_receive}, {'_id': False}))

    # 1. db.todo_tags에서 num을 조회
    # 2. db.todo에서 num을 조회
    # 3. 둘 모두 해당하지 않는 num를 새로운 todo의 num로 지정한다.
    num_list = []  # num 속성 중복 오류를 막기 위함
    for tag in tag_list:
        num_list.append(tag['num'])
    for todo in todo_list:
        num_list.append(todo['num'])

    count = len(tag_list) + 1
    while count in num_list:
        count += 1
    print(num_list, count, 'todo#{} created'.format(count))

    doc = {
        'date': date_receive,
        'num': count,
        'todo': todo_receive,
        'done': 0,  # default
        'comment': '',  # default
        'tag': []  # default
    }
    db.todo.insert_one(doc)
    print('<new todolist created>\nDate: {}, todo: {} Num: {} -> db.todo'.format(date_receive, todo_receive, count))

    # todo_percent update
    if percent_list:
        done_count = percent_list[0]['done_count']
        total = percent_list[0]['total']+1
        percent_level = return_percent_level(done_count, total)
        db.todo_percent.update_one({'date': date_receive}, {'$set': {'percent_level': percent_level,
                                                                     'done_count': done_count,
                                                                     'total': total}})
        print(total, done_count, percent_level)
    else:

        doc = {
            'date': date_receive,
            'percent_level': 0,
            'done_count': 0,
            'total': 1
        }
        db.todo_percent.insert_one(doc)
        print("todo_percent : default")

    return jsonify({'msg': '등록 완료'})


@app.route("/todo/done", methods=["POST"])
def todo_done():
    num_receive = request.form['num_give']
    date_receive = request.form['date_give']
    db.todo.update_one({'num': int(num_receive)}, {'$set': {'done': 1}})
    print('#{} done!!'.format(num_receive))

    todo_list = list(db.todo.find({'date': date_receive}, {'_id': False}))
    tag_list = list(db.todo_tags.find({'num': int(num_receive)}, {'_id': False}))

    for todo in todo_list:
        # 테그 저장 부분
        if todo['tag']:  # todo에 tag가 저장되있다면
            if len(tag_list) != 0:
                print("기존 tag 수정")

                for tags in tag_list:  # 그 todo의 num가 todo_tags 에 있다면 tag 수정
                    if todo['num'] == tags['num']:
                        before = tags['tag']
                        after = todo['tag']
                        print('#{} tags updated\n {} -> {}'.format(tags['num'], before, after))
                        db.todo_tags.update_one({'num': todo['num']}, {'$set': {'tag': todo['tag']}})

            else:  # 신규 저장 이라면
                print("신규 tag 저장")
                doc = {
                    'date': todo['date'],
                    'todo': todo['todo'],
                    'num': todo['num'],
                    'tag': todo['tag'],
                    'comment': todo['comment']
                }

                db.todo_tags.insert_one(doc)

                print('new tag created')
                print('#{} tags created in db.todo_tags\n {}'.format(todo['num'], todo['tag']))

    # percentage 처리 부분
    done_count = 0
    total = len(todo_list)
    for todo in todo_list:
        if todo['done'] == 1:
            done_count += 1
    percent_level = return_percent_level(done_count, total)  # percentage -> percent_level(1~5)

    print(done_count, total, 'percent_level = {}'.format(percent_level))

    done_percentage = list(db.todo_percent.find({'date': date_receive}, {'_id': False}))

    if len(done_percentage) == 0:  # new doc update

        doc = {
            'date': date_receive,
            'percent_level': percent_level,
            'done_count': done_count,
            'total': total
        }
        db.todo_percent.insert_one(doc)
        print(doc, ' \n >> db.todo_percent')
    else:  # percent_level update
        db.todo_percent.update_one({'date': date_receive}, {'$set': {'percent_level': percent_level,
                                                                     'done_count': done_count,
                                                                     'total': total}})
    print(total, done_count, percent_level)
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

    # 지난 todolist 삭제 하기
    today_date = datetime.today().strftime('%m/%d/%Y')
    # print(today_date)
    for todo in todo_list:
        # 지난 date / 완료 x / tag 입력 x 인 것 들을 삭제
        if todo['date'] != today_date:
            print(todo['num'], "deleted")
            db.todo.delete_one({'num': int(todo['num'])})

    return jsonify({'todos': todo_list})


@app.route("/todo/delete", methods=["POST"])
def todo_delete():  # todo_tags 에서 제거 하는건 쉬움 / todo_percent 에서는 고민 필요
    num_receive = request.form['num_give']
    date_receive = request.form['date_give']

    # db.todo_tags.delete_one({'num': int(num_receive)})   # todo_tags에서도 삭제.

    todo_list = list(db.todo.find({'num': int(num_receive)}, {'_id': False}))
    percent_list = list(db.todo_percent.find({'date': date_receive}, {'_id': False}))

    # doto_percent update

    total = percent_list[0]['total']-1
    done_count = percent_list[0]['done_count']

    print(todo_list)
    if todo_list[0]['done'] == 1:
        done_count -= 1

    percent_level = return_percent_level(done_count, total)
    db.todo_percent.update_one({'date': date_receive}, {'$set': {'percent_level': percent_level,
                                                                 'done_count': done_count,
                                                                 'total': total}})
    print(total, done_count, percent_level)

    db.todo.delete_one({'num': int(num_receive)})
    print('#{} deleted'.format(num_receive))

    return jsonify({'msg': '삭제 완료!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)