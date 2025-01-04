from collections.abc import Generator
from contextlib import contextmanager
from imaplib import IMAP4, IMAP4_SSL
from queue import Queue
from threading import Lock


class IMAPConnectionPool:
	_instance = None
	_lock = Lock()

	def __new__(cls, *args, **kwargs) -> "IMAPConnectionPool":
		with cls._lock:
			if cls._instance is None:
				cls._instance = super().__new__(cls, *args, **kwargs)
				cls._instance._pools = {}
				cls._instance._pool_lock = Lock()
		return cls._instance

	def get_connection(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool = True,
		max_connections: int = 5,
	) -> type[IMAP4] | type[IMAP4_SSL]:
		key = (host, port, username)
		with self._pool_lock:
			if key not in self._pools:
				self._pools[key] = Queue(max_connections)

		pool = self._pools[key]

		with Lock():
			if not pool.empty():
				return pool.get()
			if pool.qsize() < max_connections:
				return self._create_connection(host, port, username, password, use_ssl)
			raise Exception(f"IMAP connection pool limit reached for {key}")

	def return_connection(
		self, host: str, port: int, username: str, connection: type[IMAP4] | type[IMAP4_SSL]
	) -> None:
		key = (host, port, username)
		with self._pool_lock:
			if key in self._pools:
				pool = self._pools[key]
				with Lock():
					if pool.qsize() < pool.maxsize:
						pool.put(connection)
						return
		connection.logout()

	def close_all(self) -> None:
		with self._pool_lock:
			for pool in list(self._pools.values()):
				while not pool.empty():
					connection = pool.get()
					connection.logout()
			self._pools.clear()

	@staticmethod
	def _create_connection(
		host: str, port: int, username: str, password: str, use_ssl: bool
	) -> type[IMAP4] | type[IMAP4_SSL]:
		_IMAP = IMAP4_SSL if use_ssl else IMAP4

		connection = _IMAP(host, port)
		connection.login(username, password)
		return connection


class IMAPContext:
	def __init__(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool = True,
	) -> None:
		self._pool = IMAPConnectionPool()
		self._host = host
		self._port = port
		self._username = username
		self._password = password
		self._use_ssl = use_ssl
		self._connection = None

	def __enter__(self) -> type[IMAP4] | type[IMAP4_SSL]:
		self._connection = self._pool.get_connection(
			self._host, self._port, self._username, self._password, self._use_ssl
		)
		return self._connection

	def __exit__(self, exc_type, exc_value, traceback) -> None:
		if exc_type is not None:
			self._connection.logout()
		else:
			self._pool.return_connection(self._host, self._port, self._username, self._connection)


@contextmanager
def imap_server(
	host: str,
	port: int,
	username: str,
	password: str,
	use_ssl: bool = True,
) -> Generator[type[IMAP4] | type[IMAP4_SSL], None, None]:
	pool = IMAPConnectionPool()
	connection = pool.get_connection(host, port, username, password, use_ssl)

	try:
		yield connection
	finally:
		if connection:
			pool.return_connection(host, port, username, connection)
