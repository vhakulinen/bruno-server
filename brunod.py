from optparse import OptionParser
import sys
import logging
import signal
import select
import socket

from bruno.env import inputs, udp_inits
from bruno import env
from bruno.control_panel import stdin_processor
import bruno.server_utils as utils


# Global running flag
running = False


def runserver(tcp_ip, tcp_port, udp_ip, udp_port):
    global running

    tcp_address = (tcp_ip, tcp_port)
    udp_address = (udp_ip, udp_port)

    logging.debug('Creating TCP socket')
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # For proper socket closing
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    logging.info('Binding TCP %s:%s' % tcp_address)
    server_sock.bind(tcp_address)

    logging.debug('Starting to listen for clients on TCP')
    server_sock.listen(env.max_clients)

    logging.debug('Creating UDP socket')
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    logging.debug('Binding UDP %s:%s' % udp_address)
    udp_server_socket.bind(udp_address)

    running = True

    while running:
        _inputs = list(inputs.keys())
        _inputs.append(server_sock)
        _inputs.append(udp_server_socket)
        _inputs.append(sys.stdin)

        # So that we can ^C
        try:
            readable, _, expectional = select.select(_inputs, [], _inputs)
        except InterruptedError:
            continue

        for s in readable:
            if s == server_sock:
                # incoming connection
                conn, addr = server_sock.accept()
                conn.setblocking(0)  # comment this out for ssl
                logging.info('Receiced connection from %s:%s' %
                             conn.getpeername())
                inputs.update({conn: env.ClientDataContainer()})
            elif s == udp_server_socket:
                # incoming udp data
                data, addr = udp_server_socket.recvfrom(10)
                data = data.decode('utf8')
                # data == key; if key is in udp_inits, then this is valid
                # udp init call and we can save udp_port and delete
                # entry from udp_inits
                if data in udp_inits:
                    # inputs[udp_inits[data]].udp_port = addr[1]
                    inputs[udp_inits[data]].udp_addr = addr
                    del udp_inits[data]
                    # TODO: What if client disconnects and has udp_init entry?
                    # This needs to be checked on close_client()
            elif s == sys.stdin:
                data = sys.stdin.readline()
                sys.stdin.flush()
                stdin_processor(data)
            else:
                # incoming data
                logging.debug('Incoming data')
                if not inputs[s].dbuff_read:
                    utils.read_delimited_buffer(s)
                else:
                    if utils.read_content_buffer(s):
                        utils.data_processor(s)
                        inputs[s].reset_buffers()
        for s in expectional:
            logging.info('Client in exceptional state!')
            utils.close_client(s)

    for client in list(inputs.keys()):
        client.close()

    server_sock.shutdown(socket.SHUT_RDWR)
    server_sock.close()


def signal_handler(signal, frame):  # {{{
    """
        signal_handler -> None

        Handles ^C keypress and set running to false
    """
    global running
    print("Exiting...")
    running = False
signal.signal(signal.SIGINT, signal_handler)  # }}}

if __name__ == '__main__':  # {{{
    parser = OptionParser()
    parser.add_option('-i', '--ip', dest='ip', help='IP to listen',
                      default='localhost')
    parser.add_option('-t', '--tcp-port', dest='tcpport',
                      help='TCP port to listen', default='9090')
    parser.add_option('-u', '--udp-port', dest="udpport",
                      help="UDP port to listen", default='31500')
    parser.add_option('-f', '--file', dest='log_file', help='Logging file',
                      default='brunod.log')
    parser.add_option('-d', '--debug', dest='debug_level', help='DEBUG level',
                      default='INFO')
    parser.add_option('-m', '--max-clients', dest='max_clients',
                      help='Maximum number of clients', default=15)

    (options, args) = parser.parse_args()

    logging.basicConfig(filename=options.log_file, level=options.debug_level)
    env.max_clients = options.max_clients

    runserver(options.ip, int(options.tcpport), options.ip,
              int(options.udpport))  # }}}
