import inspect
import socket
from logging import getLogger

from requests import Session

socket.setdefaulttimeout(5)


class HTTPTransport(object):
    def __init__(self, ip):
        self._ip = ip

        self._session = None
        self._uuid = None

        self._logger = getLogger(self.__class__.__name__)
        self._logger.debug('{0}(); ip={1}'.format(
            inspect.currentframe().f_code.co_name, repr(ip)
        ))

    def get_uuid(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        uuid = self._session.get(
            'http://{0}/uuid'.format(self._ip),
            timeout=5,
        ).text.split(',')[-1].strip()

        self._logger.debug('{0}(); uuid={1}'.format(
            inspect.currentframe().f_code.co_name, repr(uuid)
        ))

        return uuid

    def connect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._session = Session()
        self._uuid = self.get_uuid()

        self._logger.debug('{0}(); session={1}, uuid={2}'.format(
            inspect.currentframe().f_code.co_name, self._session, repr(self._uuid)
        ))

    def call(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data),
        ))

        output = self._session.post(
            url='http://{0}/v2/{1}'.format(
                self._ip, self._uuid,
            ),
            data=data,
            timeout=5,
        ).text

        self._logger.debug('{0}({1}); output={2}'.format(
            inspect.currentframe().f_code.co_name, repr(data), repr(output)
        ))

        return output

    def disconnect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._session = None


class TCPTransport(object):
    def __init__(self, ip):
        self._ip = ip

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._logger = getLogger(self.__class__.__name__)
        self._logger.debug('{0}(); ip={1}'.format(
            inspect.currentframe().f_code.co_name, repr(ip)
        ))

    def connect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._sock.connect((self._ip, 4998))

    def call(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data),
        ))

        self._sock.send(data.encode())

        buf = self._sock.recv(1024).decode()
        if 'IR Learner Enabled' in buf:
            buf += self._sock.recv(1024).decode()

        self._logger.debug('{0}({1}); buf={2}'.format(
            inspect.currentframe().f_code.co_name, repr(data), repr(buf)
        ))

        return buf

    def disconnect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._sock.close()


class Connector(object):
    def __init__(self, transport):
        self._transport = transport

        self._logger = getLogger(self.__class__.__name__)
        self._logger.debug('{0}(); transport={1}'.format(
            inspect.currentframe().f_code.co_name, transport
        ))

    def connect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        self._transport.connect()

    def send(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        data = data.split('sendir,')[-1]

        output = self._transport.call('sendir,{0}'.format(data))

        self._logger.debug('{0}({1}); output={2}'.format(
            inspect.currentframe().f_code.co_name, repr(data), repr(output)
        ))

        return output

    def learn(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        data = self._transport.call('get_IRL')

        self._logger.debug('{0}(); data={1}'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        return data.split('sendir,')[-1]

    def disconnect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        self._transport.disconnect()


if __name__ == '__main__':
    import argparse

    import logging

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    for cls in [HTTPTransport, TCPTransport, Connector]:
        logger = logging.getLogger(cls.__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    parser = argparse.ArgumentParser(
        description='Make calls against a zmote.io device via HTTP or TCP',
        epilog='See http://www.zmote.io/apis for more detail',
    )

    parser.add_argument(
        '-t',
        '--transport',
        required=False,
        choices=['http', 'tcp'],
        default='http',
        help='transport to use for communication with the device (default HTTP)',
    )

    parser.add_argument(
        '-d',
        '--device-ip-or-hostname',
        type=str,
        required=True,
        help='IP or hostname of the device',
    )

    parser.add_argument(
        '-c',
        '--call-type',
        choices=['learn', 'send'],
        required=True,
        help='type of call to make to the device'
    )

    parser.add_argument(
        '-p',
        '--payload',
        type=str,
        default=None,
        help='payload to send (applicable for send call-type only)',
    )

    args = parser.parse_args()

    transport = None
    if args.transport == 'http':
        transport = HTTPTransport(
            ip=args.device_ip_or_hostname,
        )
    elif args.transport == 'tcp':
        transport = TCPTransport(
            ip=args.device_ip_or_hostname,
        )

    if args.call_type == 'send' and args.payload is None:
        parser.error(
            'argument -p/--payload is required when -c/--call-type is send'
        )

    connector = Connector(
        transport=transport,
    )

    connector.connect()

    if args.call_type == 'learn':
        connector.learn()
    elif args.call_type == 'send':
        connector.send(args.payload)

    connector.disconnect()
