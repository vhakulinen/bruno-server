# TODO: Fix those stupid infunction imports. Maybe do those sends in commands?
import string
import random

# from bruno.send_utils import send_error
from bruno import db


max_clients = 15
# socket: clientDataContainer
inputs = {}
# str: socket
udp_inits = {}
# length limit for delimited buffer
dbuff_limit = 8

error_codes = {99: '%s',  # Custom message
               # Basic command errors
               100: 'Unexpected error occoured',
               101: 'Unknown command',
               102: 'Invalid argument(s)\n%s',
               103: 'UDP not avaiable',
               104: 'UDP already initalized',
               105: 'UDP initializion already in progress',
               # Auth errors
               200: 'Invalid login',
               201: 'Username already in use',
               202: 'Email already in use',
               203: 'Authentication required (You\'ll need to login)',
               204: 'User is logged in somewhere else',
               # Message errors
               300: 'User or group -name invalid',
               301: 'User not online',
               # Call errors
               400: 'No call pending',
               401: 'Failed to make a call',
               }

# These are sended when command executed succesfully
command_codes = {99: '%s',  # Custom message
                 # Auth codes
                 100: 'You are now logged in as %s',
                 101: 'Logged out',
                 102: 'Registeration success',
                 # Calling
                 110: 'Call initialized',
                 111: 'Call answered',
                 112: 'Call ended',
                 # UPD init
                 120: 'UDP initializion started',
                 # Messaging
                 130: 'Message sended',
                 # Online users
                 131: '%s',
                 }


# These messages contains actual informtaion
event_codes = {'': '',
               # Messaging (p2p)
               # IP:PORT KEY
               100: '%s:%s %s',
               # KEY
               101: '%s',
               # Incoming call event
               # USERNAME
               102: '%s'
               }


def socket_by_user(user):
    """Get socket by user profile"""
    for i in inputs:
        if inputs[i].profile == user:
            return i
    return None


def socket_by_username(username, socket=None):
    """
        socket_by_username(socket, username) -> socket or None

        returns socket user if it exists and is online or None. If returns None
        will send error message to client.
    """
    def err(socket, code):
        if socket:
            # FIXME: this is just stupid to import stuff here...
            from bruno.send_utils import send_error
            send_error(socket, code)
    user = db.get_user(username)
    if user:
        if user.online:
            s = socket_by_user(user)
            if s:
                return s
            else:
                err(socket, 301)
        else:
            err(socket, 301)
    else:
        err(socket, 300)


class Call:
    ANSWERED = 1
    PENDING = 2
    caller = None
    target = None
    _state = PENDING

    def __init__(self, caller, target):
        # These needs to be sockets
        self.caller = caller
        self.target = target

        inputs[self.caller].call = self
        inputs[self.target].call = self
        # FIXME: Another stupid import
        from bruno.send_utils import send_event
        send_event(self.target, 102, (inputs[self.caller].profile.username))
        # self.caller.call = self
        # self.target.call = self

    def answer(self):
        if inputs[self.caller].udp_addr and inputs[self.target].udp_addr:
            # FIXME: This is just stupid import
            from bruno.send_utils import send_event
            self._state = self.ANSWERED
            key = ''.join(random.choice(string.ascii_lowercase)
                          for x in range(10))
            send_event(self.caller, 100,
                       (inputs[self.target].udp_addr[0],
                        inputs[self.target].udp_addr[1], key))
            send_event(self.target, 100,
                       (inputs[self.caller].udp_addr[0],
                        inputs[self.caller].udp_addr[1], key))
        else:
            # TODO: No udp avaiable
            pass

    def hangup(self):
        inputs[self.caller].call = None
        inputs[self.target].call = None
        # self.caller.call = None
        # self.target.call = None

    @property
    def state(self):
        return self.state

    @property
    def answered(self):
        if self._state == self.ANSWERED:
            return True
        else:
            return False


class ClientDataContainer(object):  # {{{
    """
        Holds client's data (but not socket).
    """
    # Database profile
    profile = None
    # Delimited buffer
    _dbuff = ''
    # Content buffer
    _cbuff = ''

    call = None
    udp_addr = None

    def reset_buffers(self):
        self._dbuff = ''
        self._cbuff = ''

    @property
    def authenticated(self):
        if self.profile:
            return True
        else:
            return False

    @property
    def dbuff_read(self):
        if len(self._dbuff) >= dbuff_limit:
            return True
        else:
            return False

    @property
    def cbuff_size(self):
        return len(self.cbuff)

    @property
    def dbuff_size(self):
        return int(self.dbuff)

    @property
    def cbuff_read(self):
        if len(self.cbuff) >= self.dbuff_size:
            return True
        else:
            return False

    @property
    def dbuff_left(self):
        return dbuff_limit - len(self.dbuff)

    @property
    def cbuff_left(self):
        return self.dbuff_size - len(self.cbuff)

    @property
    def dbuff(self):
        return self._dbuff

    @dbuff.setter
    def dbuff(self, value):
        # when doing '+=' operator, value will already be dbuff + other
        if not all([i in string.digits for i in value]):
            raise TypeError('Value must only have digits')
        if len(value) > dbuff_limit:
            raise ValueError('dbuff length may not be greater that %s (%s)' % (
                dbuff_limit, len(self._dbuff + value)))
        self._dbuff = value

    @property
    def cbuff(self):
        return self._cbuff

    @cbuff.setter
    def cbuff(self, value):
        if type(value) != str:
            self._cbuff = str(value)
        else:
            self._cbuff = value
# }}}
