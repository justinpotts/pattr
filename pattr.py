import os
from gevent import monkey
monkey.patch_all()

import time, string, random
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return render_template('index.html')

def generate_nick():
    adjectives = ['mystic', 'rustic', 'sharp', 'flowery', 'windy', 'toxic', 'serene', 'dry', 'enchanted', 'barren',
                  'tall', 'quiet', 'serene', 'noisy', 'lively', 'modern', 'old', 'crowded', 'historical', 'pleasant',
                  'dashing', 'leaping', 'running', 'eating', 'speaking', 'sleeping', 'playing', 'bouncing', 'jolly', 'mystic']

    nouns = ['mountain', 'peak', 'glacier', 'moon', 'meteor', 'forest', 'prairie', 'rock', 'grass', 'field',
             'tower', 'building', 'cafe', 'cinema', 'theater', 'cathedral', 'park', 'alley', 'avenue', 'museum',
             'jackrabbit', 'antelope', 'stallion', 'leopard', 'ocelot', 'sloth', 'polarbear', 'orca', 'shark', 'coral']

    return 'pa-' + adjectives[random.randint(0,29)] + nouns[random.randint(0,29)]

@app.route('/c/<roomcode>')
def enter_chat(roomcode):
    session['uid'] = generate_nick()
    room = roomcode
    return render_template('chat.html', room=room, uid=session['uid'])


@socketio.on('my event', namespace='')
def send_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count'], 'bot': message['bot']})


@socketio.on('join', namespace='')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1


def nick_check(nickname):
    # Restrictions for nick names: sizes, images
    restrictions = ['img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    nick_passes = True
    nick = nickname
    if '<font>' in nick and '</font>' not in nick:
        nick_passes = False
    for item in restrictions:
        if item in nick:
            nick_passes = False
    if nick_passes:
        temp_old = session['uid']
        session['uid'] = nickname
        return temp_old + ' changed nickname to ' + session['uid']
    else:
        return '@' + session['uid'] + ' Error in changing nick. Click <a href="#howto">here</a> for more information.'


@socketio.on('send message', namespace='')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    if message['data'][:5] == '/nick':
        emit('my response',
             {'data': nick_check(message['data'][6:]), 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
             room=message['room'])
    else:
        emit('my response',
         {'data': message['data'], 'count': session['receive_count'], 'sender': session['uid']},
         room=message['room'])


@socketio.on('disconnect request', namespace='')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    disconnect()
    return redirect('/index')


@socketio.on('connect', namespace='')
def connect():
    emit('my response', {'data': 'Connection successful...', 'count': 0, 'bot': 'true'})



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 33507)))
