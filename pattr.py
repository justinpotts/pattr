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
    animals = ['buffalo', 'wildebeest', 'kudu', 'springbok', 'impala', 'antelope', 'lion', 'leopard', 'cheetah', 'serval',
               'mongoose', 'elephant', 'giraffe', 'hyaena', 'jackal', 'rhino', 'zebra', 'crocodile']

    adjectives = ['mystic', 'rustic', 'sharp', 'toxic', 'enchanted', 'quiet', 'noisy', 'lively', 'modern',
                  'old', 'pleasant', 'dashing', 'leaping', 'running', 'eating', 'speaking', 'sleeping', 'playing', 'bouncing',
                  'jolly', 'mystic']

    return 'pa-' + adjectives[random.randint(0,len(adjectives)-1)] + animals[random.randint(0,len(animals)-1)]

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
    if '<' not in nickname or '>' not in nickname:
        temp_old = session['uid']
        session['uid'] =  "".join(nickname.split())
        return temp_old + ' changed nickname to ' + session['uid']
    else:
        return '@' + session['uid'] + ' Error: nickname uses restricted characters. To learn more, type <code>/help</code>.'


@socketio.on('send message', namespace='')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    if message['data'][:5] == '/nick':
        emit('my response',
             {'data': nick_check(message['data'][6:]), 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
             room=message['room'])
    elif message['data'][:5] == '/help':
        help_text = '\
        <h2><strong>Help</strong></h2>\
        <p><b>Change Nickname:</b> /nick</p>\
        <p>Nicknames cannot contain HTML such as <code>h1</code>, <code>img</code>, or <code>font</code>. However, it may contain\
        tags such as <code>href</code>, color, and font awesome icons.</p>\
        <p>A detailed HTML guide can be found <a href="https://developer.mozilla.org/en-US/docs/Web/HTML/Element">here</a>.</p>'
        emit('my response',
             {'data': help_text, 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
             room=message['room'])
    elif message['data'][:6] == '/about':
         about_text = '\
         <h2><strong>About</strong></h2> \
         <p><span style="font-family:Aller">pattr</span> was developed by \
         <a href="https://twitter.com/PottsJustin">Justin Potts</a>, and <a href="https://twitter.com/thealexmeza">Alex Meza</a> \
         under the BSD Open Source license.</p> \
         <p>Visit the GitHub repository <a href="https://github.com/justinpotts/pattr">here</a>, or send us a message at \
         <a href="mailto:pattr@pattr.me">pattr@pattr.me</a>.'
         emit('my response',
              {'data': about_text, 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
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
