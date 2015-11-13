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

connected_users = []


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
    session['room'] = roomcode
    return render_template('chat.html', room=session['room'], uid=session['uid'])


@socketio.on('join', namespace='')
def join(message):
    join_room(message['room'])
    session['room'] = message['room']
    session['receive_count'] = session.get('receive_count', 0) + 1
    indiv_msg = 'Joined room /c/' + session['room'] + '. For help, type <code>/help</code>. To learn more about Pattr, type <code>/about</code>.'
    gr_msg = session['uid'] + ' has joined the room.'
    emit('my response',
         {'data': indiv_msg, 'count': session['receive_count'], 'bot': 'true'},
         room=session['uid'])
    emit('my response',
         {'data': gr_msg, 'count': session['receive_count'], 'bot': 'true'},
         room=session['room'])

def nick_passes(nickname):
    if '<' in nickname or '>' in nickname:
        return False
    else:
        return True


@socketio.on('send message', namespace='')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    if message['data'][:5] == '/nick':
        nick = message['data'][5:]
        if '<' not in nick or '>' not in nick:
            temp_old = session['uid']
            session['uid'] =  "".join(nick.split())
            leave_room(temp_old)
            join_room(session['uid'])
            message['data'] = temp_old + ' changed nickname to ' + session['uid']
            emit('my response',
                 {'data': message['data'], 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
                 room=session['room'])
        else:
            message['data'] = 'Error: Nickname uses restricted characters. To learn more, type <code>/help</code>.'
            emit('my response',
                 {'data': message['data'], 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
                 room=session['uid'])

    elif message['data'][:2] == '/w':
        msg = message['data'][2:].split(' ')
        emit('my response',
             {'data': msg[2], 'count': session['receive_count'], 'whisper': 'true', 'target':msg[1], 'sender': session['uid']},
             room=msg[1])
        emit('my response',
             {'data': msg[2], 'count': session['receive_count'], 'whisper': 'true', 'target':msg[1], 'sender': session['uid']},
             room=session['uid'])

    elif message['data'][:5] == '/help':
        help_text = '\
        <h2><strong>Help</strong></h2>\
        <p><b>Change Nickname:</b> <code>/nick nickname</code></p>\
        <p>Nicknames cannot contain HTML such as <code>h1</code>, <code>img</code>, or <code>font</code>. However, it may contain\
        tags such as <code>href</code>, color, and font awesome icons. Any spaces in the nickname will be removed.</p>\
        <p><b>Whisper (Private message):</b> <code>/w targetnick message</code></p>\
        <p>A whisper is a private message and can only be seen by the user with the target nickname.</p>\
        <p><b>HTML</b></p>\
        <p>A detailed HTML guide can be found <a href="https://developer.mozilla.org/en-US/docs/Web/HTML/Element">here</a>.</p>'
        emit('my response',
             {'data': help_text, 'count': session['receive_count'], 'bot': 'true', 'sender': session['uid']},
             room=session['uid'])

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
              room=session['uid'])

    elif message['data'][:5] == '/quit':
          disconnect_text = session['uid'] + ' has left the room.'
          emit('disconnect_request')

    else:
        emit('my response',
         {'data': message['data'], 'count': session['receive_count'], 'sender': session['uid']},
         room=session['room'])


@socketio.on('disconnect request', namespace='')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    disconnect()
    return redirect('/index')


@socketio.on('connect', namespace='')
def connect():
    join_room(session['uid'])
    emit('my response', {'data': 'Connection successful...', 'count': 0, 'bot': 'true'})



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 33507)))
