"""
    commands dictinary holds all command names avaiable as strings.
    Each key has another dict as its entry which contains followind data:
        'func' = callable function for the command
        'args' = list or str, this defines if func takes it's args as string
                 or as list
    Each command method takes socket and args as arguments

    send_msg method sends message to user/group
"""
import logging
import random
import string

from bruno.send_utils import (send_srv_message, send_error, send_cmd_success,
                              send_message, send_event)
from bruno.db import auth
from bruno.db.models import User
from bruno import db
from bruno.commands.decorators import Args, auth_required, udp_required
from bruno.env import (inputs, Call, udp_inits, socket_by_username,
                       call_between, socket_by_user)

commands = {}


def send_msg(socket, args):
    """This will send the normal txt messages"""
    if args.get('user'):
        # message to user
        content = args.get('content')
        sock = socket_by_username(args.get('user'), socket)
        if sock:
            send_message(sock, inputs[socket].profile.username, content)
            send_cmd_success(socket, 130)
    else:
        # TODO: Group message
        pass

# Here starts the commads


@auth_required
def echo(socket, args):
    logging.debug('Echoing args')
    send_cmd_success(socket, 99, "Echoed")
    send_srv_message(socket, args)
commands.update({'echo': {'func': echo, 'args': str}})


@auth_required
def udp_init(socket, args):
    if inputs[socket].udp_addr:
        send_error(socket, 104)
    elif socket in list(udp_inits.values()):
        send_error(socket, 105)
    else:
        key = ''.join(random.choice(string.ascii_lowercase) for x in range(10))
        # Rest of this happens in brunod.py
        udp_inits.update({key: socket})
        send_cmd_success(socket, 120)
        send_event(socket, 101, (key))
commands.update({'udp_init': {'func': udp_init, 'args': list}})


@auth_required
def online_users(socket, args):
    output = ''
    for i in inputs:
        if inputs[i].profile:
            output += '%s %s;' % (inputs[i].profile.username, str(True))
    send_cmd_success(socket, 131, output)
commands.update({'users': {'func': online_users, 'args': list}})


# {{{ Friend requests
@auth_required
@Args(2, 'Syntax: <username>')
def friend_request_send(socket, args):
    target = db.get_user(args[1])
    if target:
        if target not in inputs[socket].profile.friends:
            if target not in inputs[socket].profile.requests and\
                    inputs[socket].profile not in target.requests:
                target.requests.append(inputs[socket].profile)
                send_cmd_success(socket, 140)
                # Lets notify the user that it has new friend request
                if target.online:
                    sock = socket_by_user(target)
                    if sock:
                        send_event(sock, 110, inputs[socket].profile.username)
            else:
                send_error(socket, 222)
        else:
            send_error(socket, 221)
    else:
        send_error(socket, 220)
commands.update({'friend_request_send': {'func': friend_request_send,
                                         'args': list}})


@auth_required
@Args(2, 'Syntax: <username>')
def friend_request_accept(socket, args):
    target = db.get_user(args[1])
    if target:
        if target in inputs[socket].profile.requests:
            # Remove request
            inputs[socket].profile.requests.remove(target)
            # Add users to eachothers friends lists
            inputs[socket].profile.friends.append(target)
            target.friends.append(inputs[socket].profile)
            send_cmd_success(socket, 141)
            if target.online:
                s = socket_by_user(target)
                if s:
                    send_event(s, 111, inputs[socket].profile.username)
                    send_event(socket, 111, target.username)
        else:
            send_error(socket, 223)
    else:
        send_error(socket, 220)
commands.update({'friend_request_accept': {'func': friend_request_accept,
                                           'args': list}})
# }}}


# {{{ Calling commands
@auth_required
@udp_required
@Args(2, 'Syntax: <username>')
def call(socket, args):
    target = socket_by_username(args[1], socket)
    if target:
        if not call_between(socket, target):
            if inputs[target].udp_addr:
                Call(caller=socket, target=target)
                send_cmd_success(socket, 110)
            else:
                send_error(socket, 401)
        else:
            send_error(socket, 402)
commands.update({'call': {'func': call, 'args': list}})


@auth_required
@Args(2, 'Syntax: <username>')
def answer(socket, args):
    def pending(socket, target):
        call = call_between(socket, target)
        if call and not call.answered:
            return call
        return False
    target = socket_by_username(args[1], socket)
    if target:
        # call = inputs[socket].call_pending(target)
        call = pending(socket, target)
        if call:
            send_cmd_success(socket, 111)
            call.answer()
        else:
            send_error(socket, 400)
commands.update({'answer': {'func': answer, 'args': list}})


@auth_required
@Args(2, 'Syntax: <username>')
def hangup(socket, args):
    target = socket_by_username(args[1], socket)
    if target:
        call = call_between(socket, target)
        if call:
            call.hangup()
            send_cmd_success(socket, 112)
        else:
            send_error(socket, 403)
commands.update({'hangup': {'func': hangup, 'args': list}})
# }}}


# {{{ Auth commands
@Args(3)
def login(socket, args):
    logging.debug('Processing login')
    user = db.get_user(args[1])
    if user and user.online is True:
        send_error(socket, 204)
    elif user and user.valid_password(args[2]):
        auth.login(socket, user)
        send_cmd_success(socket, 100, user.username)
        send_event(socket, 99, (''.join([' %s:%s' % (f.username, f.online)
                                         # [1:] so we dont send extra space
                                         for f in user.friends])[1:],
                                ''.join([r.username for r in user.requests])))
        # Notify user's friends of its login
        for friend in user.friends:
            if friend.online:
                s = socket_by_user(friend)
                if not s:
                    continue
                send_event(s, 111, user.username)
    else:
        send_error(socket, 200)
commands.update({'login': {'func': login, 'args': list}})


@auth_required
def logout(socket, args):
    logging.debug('Precessing logout')
    user = inputs[socket].profile
    auth.logout(socket, user=user)
    send_cmd_success(socket, 101)
    # Notify user's friends of its logout
    for friend in user.friends:
        if friend.online:
            s = socket_by_user(friend)
            if not s:
                continue
            send_event(s, 112, user.username)
commands.update({'logout': {'func': logout, 'args': list}})


@Args(3)
def register(socket, args):
    logging.debug('Processing registeration')
    if not db.get_user(args[1]):
        try:
            User(username=args[1], password=args[2]).save()
        except ValueError as e:
            if e.args[0]['field'] == 'username':
                send_error(socket, 205)
            elif e.args[0]['field'] == 'password':
                send_error(socket, 206)
            else:
                raise Exception("Unhandeled error while creating User!")
        else:
            send_cmd_success(socket, 102)
    else:
        send_error(socket, 201)
commands.update({'register': {'func': register, 'args': list}})
# }}}
