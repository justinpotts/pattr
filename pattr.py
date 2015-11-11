#!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time, string, random
from threading import Thread
from flask import Flask, render_template, session, request, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    x = 0

@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')


@app.route('/c/<roomcode>')
def enter_chat(roomcode):
    session['uid'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(36))
    room = roomcode
    return render_template('chatnew.html', room=room, uid=session['uid'])


@socketio.on('my event', namespace='')
def send_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count'], 'bot': message['bot']})


@socketio.on('join', namespace='')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1


@socketio.on('send message', namespace='')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count'], 'sender': session['uid']},
         room=message['room'])


@socketio.on('set nick')
def set_nick(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    session['nick'] = message['data']


@socketio.on('disconnect request', namespace='')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()
    return redirect('/index')


@socketio.on('connect', namespace='')
def connect():
    emit('my response', {'data': 'Connection successful...', 'count': 0, 'bot': 'true'})



if __name__ == '__main__':
    socketio.run(app, debug=True)
