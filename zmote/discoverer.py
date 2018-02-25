import inspect
import socket
import time
from logging import getLogger

import struct

socket.setdefaulttimeout(30)

_GROUP = '239.255.250.250'
_RECEIVE_PORT = 9131
_SEND_PORT = 9130


class Discoverer(object):
    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        mreq = struct.pack(
            "4sL",
            socket.inet_aton(_GROUP),
            socket.INADDR_ANY
        )
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self._logger = getLogger(self.__class__.__name__)
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

    def bind(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._sock.bind((_GROUP, _RECEIVE_PORT))

    def send(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.sendto(b'SENDAMXB', (_GROUP, _SEND_PORT))

    def receive(self):
        data = self._sock.recv(1024)

        self._logger.debug('{0}(); data={1}'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        return data

    def parse(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        data = data.decode('ascii')

        if not data.startswith('AMXB') or not all(
                [x in data for x in ['UUID', 'Type', 'Make', 'Model', 'Revision', 'Config-URL']]
        ):
            exception = ValueError(
                'cannot parse data {0}; does not appear to be in correct format'.format(
                    repr(data)
                )
            )

            self._logger.error('{0}({1}); exception={1}'.format(
                inspect.currentframe().f_code.co_name, repr(data)
            ))

            raise exception

        data = dict([x[0:-1].split('=') for x in data.split('<-')[1:]])

        self._logger.debug('{0}({1}); data={1}'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        return data

    def discover(self, unique_zmote_limit=None, uuid_to_look_for=None):
        if unique_zmote_limit is not None and uuid_to_look_for is not None:
            raise ValueError('must specify only one (or neither) of unique_zmote_limit or uuid_to_look_for')

        zmotes_by_uuid = {}

        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, unique_zmote_limit
        ))

        def keep_waiting():
            if unique_zmote_limit is not None:
                if len(zmotes_by_uuid) >= unique_zmote_limit:
                    return False
            elif uuid_to_look_for in zmotes_by_uuid:
                return False

            return True

        while keep_waiting():
            try:
                data = self.receive()
            except socket.timeout:
                break

            parsed_data = self.parse(data)

            ip = parsed_data.get('Config-URL').split('//')[-1].strip('/')
            parsed_data.update({
                'IP': ip,
            })

            zmotes_by_uuid.update({
                parsed_data['UUID']: parsed_data,
            })

        self._logger.debug('{0}({1}); zmotes_by_uuid={2}'.format(
            inspect.currentframe().f_code.co_name, unique_zmote_limit, zmotes_by_uuid
        ))

        return zmotes_by_uuid


def passive_discover_zmotes(unique_zmote_limit=None, uuid_to_look_for=None):
    d = Discoverer()
    d.bind()
    return d.discover(
        unique_zmote_limit=unique_zmote_limit,
        uuid_to_look_for=uuid_to_look_for,
    )


def active_discover_zmotes(unique_zmote_count=None, uuid_to_look_for=None):
    d = Discoverer()
    d.bind()
    for i in range(0, 5):
        d.send()
        time.sleep(0.1)
    return d.discover(
        unique_zmote_limit=unique_zmote_count,
        uuid_to_look_for=uuid_to_look_for,
    )


if __name__ == '__main__':
    import argparse
    import pprint

    import logging

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    logger = logging.getLogger(Discoverer.__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    parser = argparse.ArgumentParser(
        description='Discover zmote.io devices on the local network- default behaviour with no arguments is to time out after 30 seconds',
        epilog='See http://www.zmote.io/apis for more detail'
    )

    parser.add_argument(
        '-l',
        '--unique-zmote-limit',
        type=int,
        default=None,
        help='number of unique devices to wait for',
    )

    parser.add_argument(
        '-u',
        '--uuid-to-look-for',
        type=str,
        default=None,
        help='UUID of a device to wait for',
    )

    parser.add_argument(
        '-a',
        '--active',
        action='store_true',
        required=False,
        help='send probe first to discover devices faster (default disabled)',
    )

    args = parser.parse_args()

    if args.unique_zmote_limit is not None and args.uuid_to_look_for is not None:
        parser.error('must specify only one (or neither) of --unique-zmote-limit or --uuid-to-look-for')

    if args.active:
        zmotes = active_discover_zmotes(args.unique_zmote_limit, args.uuid_to_look_for)
    else:
        zmotes = passive_discover_zmotes(args.unique_zmote_limit, args.uuid_to_look_for)

    print('')
    pprint.pprint(zmotes)
