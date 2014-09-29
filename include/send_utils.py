"""
    This module contains utilitys for sending data to client sockets.
"""
import json
import logging

from include.env import dbuff_limit, error_codes, command_codes, event_codes


def send(socket, data):
    """
        send(socket, data) -> None

        Sends delimited buffer and actual data to client.
        Use this instead of socket.send().
    """
    bufflen = get_buff_len(data).encode('utf8')
    data = data.encode('utf8')
    logging.debug('Sending %s to client %s' % (data, socket.getpeername()))
    try:
        socket.send(bufflen)
        socket.send(data)
    except Exception as err:
        # TODO: Broken pipe error!
        logging.warning(err)


def send_srv_message(socket, msg):
    """
        send_srv_message(socket, msg) -> None

        Sends server message to client.
    """
    data = json_msg(msg)
    send(socket, data)


def send_message(socket, _from, msg):
    """
        send_message(socket, _from, msg) -> None

        Sends message to client.
    """
    data = json_msg(msg, _from)
    send(socket, data)


def send_error(socket, errcode, msg=None):
    """
        send_error(socket, errcode, msg=None) -> None

        Send error message to client
    """
    data = json_err(errcode, msg)
    send(socket, data)


def send_cmd_success(socket, cmdcode, content=None):
    """
        send_cmd_success(socket, cmdcode, content=None) -> None

        Send success message after command is executed
    """
    data = json_cmd_success(cmdcode, content)
    send(socket, data)


def send_event(socket, code, args):
    """
        send_event(socket, code, args) -> None

        Send event to client. args must be touple and contain right amount
        of variables for the message (check env.command_codes).
    """
    data = json_event(code, args)
    send(socket, data)


def json_event(code, args):
    """
        json_event(code, args) -> json

        Returns JSON data formated for event message
    """
    return json.dumps({'type': 'event', 'code': code,
                       'content': event_codes[code] % args})


def json_msg(content, _from=''):
    """
        json_data(data, _from='') -> json

        Returns JSON data formated for message format to be sent to client
    """
    return json.dumps({'type': 'msg', 'from': _from, 'content': content})


def json_err(errcode, msg=None):
    """
        json_error(errcode) -> None

        Returns JSON data formated for error messages to be sent to client
    """
    if msg:
        return json.dumps({'type': 'err', 'code': errcode,
                           'content': error_codes[errcode] % msg})
    return json.dumps({'type': 'err', 'code': errcode,
                       'content': error_codes[errcode]})


def json_cmd_success(cmdcode, content):
    """
        json_cmd_success(cmdcode, content) -> None

        Returns JSON data formated for success message to be sent to client
    """
    if content:
        return json.dumps({'type': 'cmd', 'code': cmdcode,
                           'content': command_codes[cmdcode] % content})
    return json.dumps({'type': 'cmd', 'code': cmdcode,
                       'content': command_codes[cmdcode]})


def get_buff_len(data):
    """
        get_buff_len(data) -> int

        Returns delimited buffer of data.
    """
    if len(data) > int('9' * dbuff_limit):
        raise ValueError
    return '0' * (dbuff_limit - len(str(len(data)))) + str(len(data))
