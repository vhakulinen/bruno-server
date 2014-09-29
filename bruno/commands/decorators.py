from bruno.send_utils import send_error
from bruno.env import inputs


class Args:
    """
        Decorator for validating number of args. You can also pass in help
        message.
    """
    def __init__(self, no_args, msg=None):
        self.no_args = no_args
        if msg:
            self.msg = '(' + msg + ')'
        else:
            self.msg = None

    def __call__(self, func):
        def wrapper(socket, args):
            if self.no_args == len(args):
                func(socket, args)
            else:
                send_error(socket, 102,
                           'Invalid arguments ' + self.msg if self.msg else '')
        return wrapper


class auth_required:
    """
        Decorator for checking if client has loged in. If not, sends auth error
        to client.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, socket, *args, **kwargs):
        if inputs[socket].profile:
            self.func(socket, *args, **kwargs)
        else:
            send_error(socket, 203)


class udp_required:
    """
        Decorator for chekcing if client has gave us udp connection. If not
        sends error to client.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, socket, *args, **kwargs):
        if inputs[socket].udp_addr:
            self.func(socket, *args, **kwargs)
        else:
            send_error(socket, 103)
