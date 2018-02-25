import unittest

import copy
from hamcrest import assert_that, equal_to
from mock import patch, call, MagicMock

from zmote.discoverer import Discoverer

_UUID = 'CI00a1b2c3'

_TEST_RESPONSE = 'AMXB<-UUID={0}><-Type=ZMT2><-Make=zmote.io><-Model=ZV-2><-Revision=2.1.4><-Config-URL=http://192.168.1.12>'.format(
    _UUID
).encode('iso-8859-1')

_TEST_RESPONSE_PARSED = {
    'UUID': 'CI00a1b2c3',
    'Make': 'zmote.io',
    'Config-URL': 'http://192.168.1.12',
    'Model': 'ZV-2',
    'Type': 'ZMT2',
    'Revision': '2.1.4'
}

_TEST_RESPONSE_PARSED_WITH_IP = {
    'IP': '192.168.1.12',
    'UUID': 'CI00a1b2c3',
    'Make': 'zmote.io',
    'Config-URL': 'http://192.168.1.12',
    'Model': 'ZV-2',
    'Type': 'ZMT2',
    'Revision': '2.1.4'
}


class DiscovererTest(unittest.TestCase):
    @patch('zmote.discoverer.socket')
    def setUp(self, socket):
        socket.inet_aton.return_value = b'\xef\xff\xc0\x89'
        socket.AF_INET = 1
        socket.SOCK_DGRAM = 2
        socket.IPPROTO_UDP = 3
        socket.SOL_SOCKET = 4
        socket.SO_REUSEADDR = 5
        socket.IPPROTO_IP = 6
        socket.INADDR_ANY = 7
        socket.IP_ADD_MEMBERSHIP = 8

        self._subject = Discoverer()

        assert_that(
            socket.mock_calls,
            equal_to([
                call.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP),
                call.socket().setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
                call.inet_aton('239.255.250.250'),
                call.socket().setsockopt(
                    socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                    b'\xef\xff\xc0\x89\x00\x00\x00\x00\x07\x00\x00\x00\x00\x00\x00\x00'
                )
            ])
        )

        self._subject._sock.mock_calls = []

    def test_bind(self):
        self._subject.bind()

        assert_that(
            self._subject._sock.mock_calls,
            equal_to([
                call.bind(('239.255.250.250', 9131))
            ])
        )

    @patch('zmote.discoverer.socket')
    def test_send(self, socket):
        socket.AF_INET = 1
        socket.SOCK_DGRAM = 2
        socket.IPPROTO_UDP = 3

        self._subject.send()

        assert_that(
            socket.mock_calls,
            equal_to([
                call.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP),
                call.socket().sendto(b'SENDAMXB', ('239.255.250.250', 9130))
            ])
        )

    def test_receive(self):
        self._subject._sock.recv.return_value = _TEST_RESPONSE

        assert_that(
            self._subject.receive(),
            equal_to(_TEST_RESPONSE)
        )

    def test_parse(self):
        assert_that(
            self._subject.parse(_TEST_RESPONSE),
            equal_to(_TEST_RESPONSE_PARSED)
        )

    def test_discover_limit(self):
        self._subject.receive = MagicMock()
        self._subject.parse = MagicMock()
        self._subject.parse.return_value = copy.deepcopy(_TEST_RESPONSE_PARSED)

        assert_that(
            self._subject.discover(unique_zmote_limit=1),
            equal_to({
                _UUID: _TEST_RESPONSE_PARSED_WITH_IP,
            })
        )

    def test_discover_uuid(self):
        self._subject.receive = MagicMock()
        self._subject.parse = MagicMock()
        self._subject.parse.return_value = copy.deepcopy(_TEST_RESPONSE_PARSED)

        assert_that(
            self._subject.discover(uuid_to_look_for='CI00a1b2c3'),
            equal_to({
                _UUID: _TEST_RESPONSE_PARSED_WITH_IP,
            })
        )
