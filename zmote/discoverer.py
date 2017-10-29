import pprint
import socket
import struct


class Discoverer(object):
    def __init__(self, group='239.255.250.250', receive_port=9131, send_port=9130):
        self._group = group
        self._receive_port = receive_port
        self._send_port = send_port

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        mreq = struct.pack("4sl", socket.inet_aton(self._group), socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def bind(self):
        self._sock.bind((self._group, self._receive_port))

    def send(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.sendto('SENDAMXB', (self._group, self._send_port))

    def receive(self):
        return self._sock.recv(1024)

    @staticmethod
    def parse(data):
        if not data.startswith('AMXB') or not all([x in data for x in ['UUID', 'Type', 'Make', 'Model', 'Revision', 'Config-URL']]):
            raise ValueError(
                'cannot parse data {0}; does not appear to be in correct format'.format(
                    repr(data)
                )
            )

        return dict([x[0:-1].split('=') for x in data.split('<-')[1:]])

    def discover(self, unique_zmote_limit=1):
        zmotes_by_uuid = {}

        while len(zmotes_by_uuid) < unique_zmote_limit:
            data = self.receive()

            parsed_data = self.parse(data)

            zmotes_by_uuid.update({
                parsed_data['UUID']: parsed_data
            })

        return zmotes_by_uuid


def passive_discover_zmotes(unique_zmote_limit=1):
    d = Discoverer()
    d.bind()
    pprint.pprint(d.discover(
        unique_zmote_limit=unique_zmote_limit
    ))


def active_discover_zmotes(unique_zmote_count=1):
    d = Discoverer()
    d.bind()
    d.send()
    pprint.pprint(d.discover(
        unique_zmote_limit=unique_zmote_count
    ))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Discover zmote.io devices on the local network',
        epilog='See http://www.zmote.io/apis for more detail'
    )

    parser.add_argument(
        '-u',
        '--unique-zmote-limit',
        type=int,
        default=1,
        help='number of unique devices to wait for (default 1)',
    )

    parser.add_argument(
        '-a',
        '--active',
        action='store_true',
        required=False,
        help='send probe first to discover devices faster (default disabled)',
    )

    args = parser.parse_args()

    if args.active:
        active_discover_zmotes(args.unique_zmote_limit)
    else:
        passive_discover_zmotes(args.unique_zmote_limit)
