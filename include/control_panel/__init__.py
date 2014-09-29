from include.db import get_user
from include.db.models import User
from include.db.constants import db_session as session
from include.db.auth import logout as dblogout
from include.control_panel.decorators import Args
from include.env import inputs, socket_by_user
from include import commands as user_api

panel_commands = {}


def print_prompt():
    print(">>", end=" ", flush=True)
# So that we have prompt when we start the program
print_prompt()


def stdin_processor(data):
    """
        stdin_processor(data) -> None

        Local control panel. This function handles input from stdin and
        writes (print()) to stdout.
    """
    if len(data.strip()) == 0:
        return
    args = data.split()
    if args[0] in panel_commands:
        cmd = panel_commands[args[0]]
        if cmd.get('args') == str:
            cmd.get('func')(data)
        else:
            cmd.get('func')(args)
    else:
        print("Command not found.")
    print_prompt()


def api_commands(args):
    output = ""
    for i in user_api.commands:
        output += i if output == "" else '\n' + i
    print(output)
panel_commands.update({'api': {'func': api_commands, 'args': list}})


def users_stats(args):
    users = session.query(User).all()
    output = ""
    skel = "username: {} online: {}"
    for i in users:
        d = skel.format(i.username, i.online)
        output += d if output == "" else '\n' + d
    print(output)
panel_commands.update({'users': {'func': users_stats, 'args': list}})


@Args(2, "user <username>")
def user_stats(args):
    user = get_user(args[1])
    if user:
        print("username: {} online: {}".format(user.username, user.online))
    else:
        print("User not found!")
panel_commands.update({'user': {'func': user_stats, 'args': list}})


@Args(2, "udp <username>")
def user_udp(args):
    for i in inputs:
        if inputs[i].profile and inputs[i].profile.username == args[1]:
            print(inputs[i].udp_addr)
            return
    print("user not connected")
panel_commands.update({'udp': {'func': user_udp, 'args': list}})


@Args(2, 'logout <username>')
def logout(args):
    user = get_user(args[1])
    if user:
        s = socket_by_user(user)
        if s:
            dblogout(s, user)
        else:
            user.online = False
panel_commands.update({'logout': {'func': logout, 'args': list}})
