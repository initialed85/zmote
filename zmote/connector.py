import socket

from requests import Session


class HTTPTransport(object):
    def __init__(self, ip):
        self._ip = ip

        self._session = None
        self._uuid = None

    def get_uuid(self):
        return self._session.get(
            'http://{0}/uuid'.format(self._ip)
        ).text.split(',')[-1].strip()

    def connect(self):
        self._session = Session()
        self._uuid = self.get_uuid()

    def call(self, data):
        return self._session.post(
            url='http://{0}/v2/{1}'.format(
                self._ip, self._uuid,
            ),
            data=data,
        ).text

    def disconnect(self):
        self._session = None


class TCPTransport(object):
    def __init__(self, ip):
        self._ip = ip

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self._sock.connect((self._ip, 4998))

    def call(self, data):
        self._sock.send(data)

        buf = self._sock.recv(1024)
        if 'IR Learner Enabled' in buf:
            buf += self._sock.recv(1024)

        return buf

    def disconnect(self):
        self._sock.close()


class Connector(object):
    def __init__(self, transport):
        self._transport = transport

    def connect(self):
        self._transport.connect()

    def send(self, data):
        data = data.split('sendir,')[-1]

        return self._transport.call('sendir,{0}'.format(data))

    def learn(self):
        data = self._transport.call('get_IRL')

        return data.split('sendir,')[-1]

    def disconnect(self):
        self._transport.disconnect()


if __name__ == '__main__':
    import argparse

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
        print 'waiting for learn response...'
        print connector.learn()
    elif args.call_type == 'send':
        print 'sending {0}'.format(repr(args.payload))
        print connector.send(args.payload)

    connector.disconnect()
