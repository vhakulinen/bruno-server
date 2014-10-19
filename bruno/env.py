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
               205: 'Username must be atleast 3 characters long',
               206: 'Password must be atleast 3 characters long',
               # Friend requests
               220: 'User doesn\'t exist',
               221: 'User already in friends',
               222: 'Friend request exists already',
               223: 'No such request',
               # Message errors
               300: 'User or group -name invalid',
               301: 'User not online',
               # Call errors
               400: 'No call to answer',
               401: 'Failed to make a call',
               402: 'Dubplicated call',
               403: 'No call to end',
               }

# These are sended when command executed succesfully
command_codes = {99: '%s',  # Custom message
                 # Auth codes
                 100: 'You are now logged in as %s',
                 101: 'Logged out',
                 102: 'Registeration success',
                 # Calling
                 110: 'Call initialized',
                 111: 'Answering the call',
                 112: 'Hangingup the call',
                 # UPD init
                 120: 'UDP initializion started',
                 # Messaging
                 130: 'Message sended',
                 # Online users
                 131: '%s',
                 # Friend requests
                 140: 'Friend request sended',
                 141: 'Friend request accepted',
                 142: 'Friend request rejected',
                 }


# These messages contains actual informtaion
event_codes = {'': '',
               # Login
               # <list of friends>;<list of friendrequests>
               # list of friends: <username>:<online>
               # list of requests: <username>
               99: '%s;%s',
               # UDP hole puch
               # IP:PORT KEY
               100: '%s:%s %s',
               # KEY
               101: '%s',
               # Incoming call event
               # USERNAME
               102: '%s',
               # Call hangedup
               # USERNAME
               103: '%s',
               # New friend request
               # USERNAME
               110: '%s',
               # Friend login
               # USERNAME
               111: '%s',
               # Friend logout
               # USERNAME
               112: '%s',
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


def call_between(socket, target):
    """
        call_between(socket, target) -> Call/None

        Checks inputs[socket].calls for existing call where partakers are
        socket and target. If finds one, returns the call object, else returns
        None.
    """
    for call in inputs[socket].calls:
        if set([socket, target]) == set(call.partakers):
            return call
    return None


def notify_friends(user, code, content=""):
    """
        notify_friends(user) -> None

        user = db.models.User
        code = int (event code)
        content = str (if there is content to event message, add it here)

        Sends event as notify to all user.friends. Requires that friend is
        online and in inputs in order to evet to be sended
    """
    from bruno.send_utils import send_event
    for friend in user.friends:
        if friend.online:
            s = socket_by_user(friend)
            if not s:
                continue
            send_event(s, code, content)


class Call:  # {{{
    ANSWERED = 1
    PENDING = 2
    caller = None
    target = None
    _state = PENDING

    def __init__(self, caller, target):
        # These needs to be sockets
        self.caller = caller
        self.target = target

        inputs[self.caller].calls.append(self)
        inputs[self.target].calls.append(self)
        # FIXME: Another stupid import
        from bruno.send_utils import send_event
        send_event(self.target, 102, (inputs[self.caller].profile.username))

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
        from bruno.send_utils import send_event
        inputs[self.caller].calls.remove(self)
        inputs[self.target].calls.remove(self)
        send_event(self.caller, 103, inputs[self.target].profile.username)
        send_event(self.target, 103, inputs[self.caller].profile.username)

    @property
    def partakers(self):
        return [self.caller, self.target]

    @property
    def state(self):
        return self.state

    @property
    def answered(self):
        if self._state == self.ANSWERED:
            return True
        else:
            return False
# }}}


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

    calls = []
    udp_addr = None

    def reset_buffers(self):
        self._dbuff = ''
        self._cbuff = ''

    def call_pending(self, user):
        # Check if there is call peding with user
        for call in self.calls:
            # If call.caller == user, then the user is calling us
            # notthe other way araound
            if call.PENDING and call.caller == user:
                return call
        return None

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
