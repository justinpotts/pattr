#!/usr/bin/env python

import os
from gevent import monkey
monkey.patch_all()

import string
import random
from cgi import escape
from flask import Flask, render_template, session, request, redirect
from flask_socketio import SocketIO, emit, join_room, disconnect
import stripe

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None

stripe_keys = {
    'publishable_key': os.environ.get("PUBLISHABLE_KEY"),
    'secret_key': os.environ.get("SECRET_KEY")
}

stripe.api_key = stripe_keys['secret_key']

connected_users = {}


@app.route('/')
def index():
    return render_template('index.html', key=stripe_keys['publishable_key'])


@app.route('/tos')
def tos():
    return render_template('tos.html')


def generate_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(36))


def generate_nick():
    animals = ['buffalo', 'wildebeest', 'kudu', 'springbok', 'impala', 'antelope', 'lion', 'leopard', 'cheetah', 'serval',
               'mongoose', 'elephant', 'giraffe', 'hyaena', 'jackal', 'rhino', 'zebra', 'crocodile']

    adjectives = ['mystic', 'rustic', 'sharp', 'toxic', 'enchanted', 'quiet', 'noisy', 'lively', 'modern',
                  'old', 'pleasant', 'dashing', 'leaping', 'running', 'eating', 'speaking', 'sleeping', 'playing', 'bouncing',
                  'jolly', 'mystic']

    return 'pa-' + adjectives[random.randint(0, len(adjectives) - 1)] + animals[random.randint(0, len(animals) - 1)]


@app.route('/c/<roomcode>')
def enter_chat(roomcode):
    if request.url == 'http://pattr.me/c/' + roomcode or request.url == 'http://www.pattr.me/c/' + roomcode:
        return redirect('http://chat.pattr.me/c/' + roomcode)
    else:
        session['uid'] = generate_id()
        session['nick'] = generate_nick()
        session['room'] = roomcode
        try:
            connected_users[session['room']][session['uid']] = session['nick']
        except KeyError:
            connected_users[session['room']] = {session['uid']: session['nick']}
        return render_template('chat.html', key=stripe_keys['publishable_key'])


@app.route('/donate', methods=['POST'])
def charge():
    # Amount in cents
    amount = 500

    customer = stripe.Customer.create(
        card=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Pattr Donation'
    )

    return redirect('/')


@socketio.on('join', namespace='')
def join(message):
    join_room(message['room'])
    session['room'] = message['room']
    indiv_msg = 'Joined room /c/' + session['room'] + '. For help, type <code>/help</code>. To learn more about Pattr, type <code>/about</code>.'
    gr_msg = session['nick'] + ' has joined the room.'
    emit('my response',
         {'data': indiv_msg, 'bot': 'true'},
         room=session['uid'])
    emit('my response',
         {'data': gr_msg, 'bot': 'true'},
         room=session['room'])


def nick_passes(nickname):
    if nickname in connected_users[session['room']].values():
        return False
    elif len(nickname) == 0:
        return False
    elif nickname == 'pattrbot':
        return False
    else:
        return True


def linkify(message):
    domain_extensions = ['.com', '.net', '.edu', '.gov',
                         '.io', '.uk', '.ca', '.de',
                         '.fr', '.us', '.it', '.biz',
                         '.xyz', '.co', '.me', '.info']
    m = message.split(' ')
    if 'http://' in message or 'https://' in message and any(ext in message for ext in domain_extensions):
        url_locs = [i for i, s in enumerate(m) if 'http://' in s]
        url_locs += [i for i, s in enumerate(m) if 'https://' in s]
        for loc in url_locs:
            m[loc] = '<a target="_blank" href="' + m[loc] + '">' + m[loc] + '</a>'
    if 'www.' in message and any(ext in message for ext in domain_extensions):
        url_locs = [i for i, s in enumerate(m) if 'www.' in s]
        for loc in url_locs:
            if 'http' not in m[loc]:
                m[loc] = '<a target="_blank" href="http://' + m[loc] + '">' + m[loc] + '</a>'
    new_message = ' '.join(m)
    return new_message


@socketio.on('send message', namespace='')
def send_room_message(message):
    message['data'] = escape(message['data'], quote=True)
    if message['data'][:1] == '/':
        if message['data'][:5] == '/nick':
            nick = "".join(message['data'][6:].split())
            if nick_passes(nick):
                temp_old = session['nick']
                session['nick'] = nick
                connected_users[session['room']][session['uid']] = nick
                message['data'] = temp_old + ' changed nickname to ' + session['nick']
                emit('my response',
                     {'data': message['data'], 'bot': 'true'},
                     room=session['room'])
            else:
                message['data'] = 'Error: Nickname is already in use, or uses restricted characters. To learn more, type <code>/help</code>.'
                emit('my response',
                     {'data': message['data'], 'bot': 'true'},
                     room=session['uid'])

        elif message['data'][:2] == '/w':
            data = message['data'][2:].split(' ')
            message = ' '.join(data[2:])
            target_uid = ''
            for item in connected_users[session['room']]:
                if connected_users[session['room']][item] == data[1]:
                    target_uid = item
            if target_uid == '':
                message = 'Cannot find user ' + data[1] + '. Type <code>/users</code> to view online users.'
                emit('my response',
                     {'data': message, 'bot': 'true'},
                     room=session['uid'])
            elif target_uid == session['uid']:
                message = 'You may not send a whipser to yourself. Type <code>/users</code> to view online users.'
                emit('my response',
                     {'data': message, 'bot': 'true'},
                     room=session['uid'])
            else:
                message = linkify(message)
                emit('my response',
                     {'data': message, 'whisper': 'true', 'target': data[1], 'sender': session['nick']},
                     room=target_uid)
                emit('my response',
                     {'data': message, 'whisper': 'true', 'target': data[1], 'sender': session['nick']},
                     room=session['uid'])

        elif message['data'][:5] == '/help':
            help_text = '\
            <h2><strong>Help</strong></h2> \
            <p><b>Change Nickname:</b> <code>/nick nickname</code></p> \
            <p>Nicknames cannot contain HTML elements or attributes, or the characters <code><</code> or <code>></code>.</p> \
            <p>Nicknames must be unique, so duplicate nicknames will produce an error.</p> \
            <p><b>Whisper (Private message):</b> <code>/w targetnick message</code></p> \
            <p>A whisper is a private message and can only be seen by the user with the target nickname.</p> \
            <p><b>Users:</b> <code>/users</code></p> \
            <p>View online users in the room.</p>'
            emit('my response',
                 {'data': help_text, 'bot': 'true'},
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
                 {'data': about_text, 'bot': 'true'},
                 room=session['uid'])

        elif message['data'][:6] == '/users':
            users = []
            for item in connected_users[session['room']]:
                users.append(connected_users[session['room']][item])
            user_list_text = '<h2><strong>Users (' + str(len(users)) + ')</strong></h2><p>' + ', '.join(sorted(users)) + '</p>'
            emit('my response',
                 {'data': user_list_text, 'bot': 'true'},
                 room=session['uid'])

        else:
            msg = 'Command not found. For more information, type <code>/help</code>.'
            emit('my response',
                 {'data': msg, 'bot': 'true'},
                 room=session['uid'])

    else:
        if '\n' in message['data']:
            msg = '<code><pre>' + message['data'] + '</pre></code>'
            emit('my response',
                 {'data': linkify(msg), 'sender': session['nick']},
                 room=session['room'])
        else:
            emit('my response',
                 {'data': linkify(message['data']), 'sender': session['nick']},
                 room=session['room'])


@socketio.on('disconnect request', namespace='')
def disconnect_request():
    session['donated'] = False
    session['receive_count'] = session.get('receive_count', 0) + 1
    indiv_msg = 'You have disconnected.'
    gr_msg = session['nick'] + ' has disconnected.'
    del connected_users[session['room']][session['uid']]
    emit('my response',
         {'data': indiv_msg, 'bot': 'true'}, room=session['uid'])
    disconnect()
    emit('my response',
         {'data': gr_msg, 'bot': 'true'}, room=session['room'])
    render_template('index.html')


@socketio.on('connect', namespace='')
def connect():
    join_room(session['uid'])
    emit('my response', {'data': 'Connection successful...', 'count': 0, 'bot': 'true'})


@app.route('/donatessl', methods=['POST'])
def donate_ssl():
    # Amount in cents
    amount = 100

    customer = stripe.Customer.create(
        card=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Pattr Donation'
    )

    session['donated'] = True
    return redirect('/')


@app.route('/ssl')
def ssl():
    return render_template('ssl.html', key=stripe_keys['publishable_key'])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', e=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', e=e), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 33507)))
