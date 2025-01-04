from collections.abc import Generator
from contextlib import contextmanager
from queue import Queue
from smtplib import SMTP, SMTP_SSL
from threading import Lock


class SMTPConnectionPool:
	_instance = None
	_lock = Lock()

	def __new__(cls, *args, **kwargs) -> "SMTPConnectionPool":
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
		use_ssl: bool = False,
		use_tls: bool = False,
		max_connections: int = 5,
	) -> type[SMTP] | type[SMTP_SSL]:
		key = (host, port, username)
		with self._pool_lock:
			if key not in self._pools:
				self._pools[key] = Queue(max_connections)

		pool = self._pools[key]

		with Lock():
			if not pool.empty():
				return pool.get()
			if pool.qsize() < max_connections:
				return self._create_connection(host, port, username, password, use_ssl, use_tls)
			raise Exception(f"SMTP connection pool limit reached for {key}")

	def return_connection(
		self, host: str, port: int, username: str, connection: type[SMTP] | type[SMTP_SSL]
	) -> None:
		key = (host, port, username)
		with self._pool_lock:
			if key in self._pools:
				pool = self._pools[key]
				with Lock():
					if pool.qsize() < pool.maxsize:
						pool.put(connection)
						return
		connection.quit()

	def close_all(self) -> None:
		with self._pool_lock:
			for pool in list(self._pools.values()):
				while not pool.empty():
					connection = pool.get()
					connection.quit()
			self._pools.clear()

	@staticmethod
	def _create_connection(
		host: str, port: int, username: str, password: str, use_ssl: bool, use_tls: bool
	) -> type[SMTP] | type[SMTP_SSL]:
		_SMTP = SMTP_SSL if use_ssl else SMTP

		connection = _SMTP(host, port)

		if use_tls:
			connection.ehlo()
			connection.starttls()
			connection.ehlo()

		connection.login(username, password)
		return connection


class SMTPContext:
	def __init__(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool = False,
		use_tls: bool = False,
	) -> None:
		self._pool = SMTPConnectionPool()
		self._host = host
		self._port = port
		self._username = username
		self._password = password
		self._use_ssl = use_ssl
		self._use_tls = use_tls
		self._connection = None

	def __enter__(self) -> SMTP | SMTP_SSL:
		self._connection = self._pool.get_connection(
			self._host, self._port, self._username, self._password, self._use_ssl, self._use_tls
		)
		return self._connection

	def __exit__(self, exc_type, exc_value, traceback) -> None:
		if exc_type is not None:
			self._connection.quit()
		else:
			self._pool.return_connection(self._host, self._port, self._username, self._connection)


@contextmanager
def smtp_server(
	host: str,
	port: int,
	username: str,
	password: str,
	use_ssl: bool = False,
	use_tls: bool = False,
) -> Generator[type[SMTP] | type[SMTP_SSL], None, None]:
	pool = SMTPConnectionPool()
	connection = pool.get_connection(host, port, username, password, use_ssl, use_tls)

	try:
		yield connection
	finally:
		if connection:
			pool.return_connection(host, port, username, connection)
