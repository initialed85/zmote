import unittest

from hamcrest import assert_that, equal_to
from mock import patch, call, MagicMock

from zmote.connector import HTTPTransport, TCPTransport
from zmote.discoverer_test import _UUID

_TEST_SENDIR_REQUEST = 'sendir,1:1,0,36000,1,1,32,32,64,32,32,64,32,3264'

_TEST_SENDIR_RESPONSE = b'completeir,1:1,0'


class HTTPTransportTest(unittest.TestCase):
    def setUp(self):
        self._subject = HTTPTransport(
            ip='192.168.1.12',
        )

        self._subject._session = MagicMock()
        self._subject._uuid = _UUID

    @patch('zmote.connector.Session')
    def test_connect(self, session):
        session.get.return_value = 'uuid,{0}'.format(_UUID)

        self._subject.connect()

        assert_that(
            session().get.mock_calls[0:1],
            equal_to([
                call('http://{0}/uuid'.format(self._subject._ip), timeout=5),
            ])
        )

    def test_call(self):
        mock_response = MagicMock()
        mock_response.text = _TEST_SENDIR_RESPONSE

        self._subject._session.post.return_value = mock_response

        assert_that(
            self._subject.call(_TEST_SENDIR_REQUEST),
            equal_to(_TEST_SENDIR_RESPONSE)
        )

        assert_that(
            self._subject._session.mock_calls,
            equal_to([
                call.post(
                    url='http://{0}/v2/{1}'.format(self._subject._ip, _UUID),
                    data=_TEST_SENDIR_REQUEST,
                    timeout=5,
                )
            ])
        )

    def test_disconnect(self):
        self._subject.disconnect()

        assert_that(
            self._subject._session,
            equal_to(None)
        )


class TCPTransportTest(unittest.TestCase):
    @patch('zmote.connector.socket')
    def setUp(self, socket):
        socket.AF_INET = 1
        socket.SOCK_STREAM = 2

        self._subject = TCPTransport(
            ip='192.168.1.12',
        )

        self._subject._sock = MagicMock()

        assert_that(
            socket.mock_calls,
            equal_to([
                call.socket(socket.AF_INET, socket.SOCK_STREAM)
            ])
        )

    def test_connect(self):
        self._subject.connect()

        assert_that(
            self._subject._sock.mock_calls,
            equal_to([
                call.connect((self._subject._ip, 4998))
            ])
        )

    def test_call(self):
        self._subject._sock.recv.return_value = _TEST_SENDIR_RESPONSE

        assert_that(
            self._subject.call(_TEST_SENDIR_REQUEST),
            equal_to(_TEST_SENDIR_RESPONSE.decode())
        )

        assert_that(
            self._subject._sock.mock_calls,
            equal_to([
                call.send(b'sendir,1:1,0,36000,1,1,32,32,64,32,32,64,32,3264'),
                call.recv(1024)
            ])
        )

    def test_disconnect(self):
        self._subject.disconnect()

        assert_that(
            self._subject._sock.mock_calls,
            equal_to([
                call.close()
            ])
        )
