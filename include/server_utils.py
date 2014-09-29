"""
This module contains utilitys for Bruno server which could be included
to brunod.py but I decided to have these in their own module for readabilty.

Mainly has utilitys for receiving and processing data from client.

Just import this to burnod.py.
"""
import logging
import json

from include.env import inputs
from include.send_utils import send_error
from include.commands import commands, send_msg
from include.db import auth


def read_delimited_buffer(socket):
    """
        read_delimited_buffer(socket) -> None

        Reads dbuff from client. Receives data from client's sockek and
        adds it to ClientDataContainer.dbuff.

        Check ClientDataContainer.dbuff_read() before calling this.

        If receives no data from client, closes the client.
    """
    logging.debug('Reading dbuff from client')
    data = receive_data(socket, inputs[socket].dbuff_left)
    if data:
        try:
            data = data.rstrip()
            inputs[socket].dbuff += data
            logging.debug('Added "%s" to dbuff', data)
            logging.debug('dbuff: %s (length: %s)', inputs[socket].dbuff,
                          len(inputs[socket].dbuff))
        except ValueError as err:
            logging.debug('ValueError while reading dbuff (%s)', err)
            close_client(socket)
        except TypeError as err:
            logging.debug('TypeError while reading dbuff (%s)', err)
            close_client(socket)
        except:
            logging.warning('Unexpected error!')
            close_client(socket)
    else:
        logging.info('Received no data from client! (dbuff)')
        close_client(socket)


def read_content_buffer(socket):
    """
        read_content_buffer(socket) -> True/False

        Reads cbuff from client. Receives data from client's socket and
        adds it to ClientDataContainer.cbuff. Be sure that dbuff is read
        before calling this.

        If returns True, content buffer is fully read from client and is ready
        to be processed. Does not reset buffers.
        If returns False, content buffer is not fully read and is not ready
        to be processed.

        Adds received data to client's content buffer either ways.

        If receives no data from client, closes the client and returns False.
    """
    logging.debug('Reading cbuff from client')
    data = receive_data(socket, inputs[socket].cbuff_left)
    if data:
        logging.debug('Got data from client (cbuff): %s', data)
        logging.debug('cbuff: %s', inputs[socket].cbuff)
        if len(data) + inputs[socket].cbuff_size < inputs[socket].dbuff_size:
            inputs[socket].cbuff += data
            logging.debug('Added "%s" to cbuff', data)
            return False
        else:
            inputs[socket].cbuff += data
            logging.debug('Added "%s" to cbuff', data)
            logging.debug('cbuff read; cbuff: %s', inputs[socket].cbuff)
            return True
    else:
        logging.info('Received no data from client! (cbuff)')
        close_client(socket)
        return False


def data_processor(socket):
    """
        data_processors(socket) -> None

        Converts cbuff to JSON. If fails, closes client.
    """
    logging.debug('Starting to process data from client')
    try:
        data_json = json.loads(inputs[socket].cbuff)
    except ValueError as err:
        logging.debug('ValueError: Failed to convert cbuff to JSON (%s)', err)
        data_json = None
    if data_json:
        try:
            validate_json_data(data_json)
        except KeyError as err:
            logging.debug('KerError: Received invalid '
                          'formated JSON data (%s).', err)
            return
        data = data_json
        if data['type'] == 'msg':
            send_msg(socket, data)
        elif data['type'] == 'cmd':
            cmd = data['args'].split()[0]
            if len(cmd) != 0:
                if cmd in commands:
                    if commands[cmd]['args'] == str:
                        commands[cmd]['func'](socket, data['args'])
                    else:
                        commands[cmd]['func'](socket, data['args'].split())
                else:
                    send_error(socket, 101)
            else:
                close_client(socket)
    else:
        close_client(socket)


def validate_json_data(data):
    """
        validate_json_data(data) -> None

        Validates
    """
    if 'type' not in data:
        raise KeyError('Type not specified!')
    if data['type'] not in ['msg', 'cmd']:
        raise KeyError('Wrong type specified')
    if data['type'] == 'msg':
        if 'user' not in data and 'group' not in data:
            # TODO: check that only other one of these is here, not both
            raise KeyError('User nor group specified in message')
        if 'content' not in data:
            raise KeyError('Content not specified in message')
    elif data['type'] == 'cmd':
        if 'args' not in data:
            raise KeyError('Args not specified in command')


def close_client(socket):
    """
        close_client(socket) -> None

        Closes client's socket and removes entry from env.inputs
    """
    logging.info('Closing client')
    if inputs[socket].profile:
        auth.logout(socket)
    socket.close()
    del inputs[socket]


def receive_data(socket, length):
    """
        receive_data(socket, length) -> data

        If data is None, error occoured or no data was received.
    """
    logging.debug('Receiving data from client')
    try:
        data = socket.recv(length)
        data = data.decode('utf-8')
    except:
        logging.debug('Error while receiving data from client')
        data = None
    return data
