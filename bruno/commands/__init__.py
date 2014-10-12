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
from bruno.env import inputs, Call, udp_inits, socket_by_username

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


# {{{ Calling commands
@auth_required
@udp_required
@Args(2, 'Syntax: <username>')
def call(socket, args):
    target = socket_by_username(args[1], socket)
    if target and not inputs[socket].call:
        if not inputs[target].call:
            if inputs[target].udp_addr:
                Call(caller=socket, target=target)
                send_cmd_success(socket, 110)
            else:
                # Target is not ready for udp
                send_error(socket, 401)
        else:
            # TODO: target is already having a call
            pass
    else:
        # TODO: You already are having a call
        pass
commands.update({'call': {'func': call, 'args': list}})


@auth_required
def answer(socket, args):
    if inputs[socket].call and not inputs[socket].call.answered:
        # The magic happens in following function
        inputs[socket].call.answer()
        send_cmd_success(socket, 111)
    else:
        # TODO: There is no call pending
        pass
commands.update({'answer': {'func': answer, 'args': list}})


@auth_required
def hangup(socket, args):
    if inputs[socket].call:
        inputs[socket].call.hangup()
        send_cmd_success(socket, 112)
    else:
        # TODO: No call to hangup
        pass
commands.update({'hangup': {'func': hangup, 'args': list}})
# }}}


# {{{ Auth commands
@Args(3)
def login(socket, args):
    logging.debug('Processing login')
    user = db.get_user(args[1])
    if user == 1:
        send_error(socket, 204)
    elif user and user.valid_password(args[2]):
        auth.login(socket, user)
        send_cmd_success(socket, 100, user.username)
    else:
        send_error(socket, 200)
commands.update({'login': {'func': login, 'args': list}})


@auth_required
def logout(socket, args):
    logging.debug('Precessing logout')
    auth.logout(socket)
    send_cmd_success(socket, 101)
commands.update({'logout': {'func': logout, 'args': list}})


@Args(3)
def register(socket, args):
    logging.debug('Processing registeration')
    if not db.get_user(args[1]):
        User(username=args[1], password=args[2]).save()
        send_cmd_success(socket, 102)
    else:
        send_error(socket, 201)
commands.update({'register': {'func': register, 'args': list}})
# }}}
