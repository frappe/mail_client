import time
from collections.abc import Generator
from contextlib import contextmanager
from imaplib import IMAP4, IMAP4_SSL
from queue import Queue
from threading import Lock, Thread

from mail.utils.cache import get_imap_limits


class IMAPConnectionLimitError(Exception):
	pass


class IMAPConnection:
	def __init__(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool,
		authenticated_timeout: int,
		unauthenticated_timeout: int,
		idle_timeout: int,
	) -> None:
		self.__authenticated_timeout = authenticated_timeout
		self.__unauthenticated_timeout = unauthenticated_timeout
		self.__idle_timeout = idle_timeout

		self.session = self.__create_connection(host, port, username, password, use_ssl)
		self.host = host
		self.port = port
		self.username = username
		self.authenticated = False
		self.idle_since = None
		self.last_used = time.time()

	def __create_connection(
		self, host: str, port: int, username: str, password: str, use_ssl: bool
	) -> IMAP4 | IMAP4_SSL:
		_IMAP = IMAP4_SSL if use_ssl else IMAP4
		session = _IMAP(host, port)
		session.login(username, password)
		self.authenticated = True
		return session

	def is_active(self) -> bool:
		try:
			self.session.noop()
			self.idle_since = None
			return True
		except Exception:
			return False

	def is_valid(self) -> bool:
		current_time = time.time()

		if self.authenticated:
			timeout = self.__authenticated_timeout
		else:
			timeout = self.__unauthenticated_timeout

		if current_time - self.last_used > timeout or (
			self.idle_since and current_time - self.idle_since > self.__idle_timeout
		):
			return False

		return self.is_active()

	def close(self) -> None:
		try:
			self.session.logout()
			self.session.shutdown()
		except Exception:
			pass


class IMAPConnectionPool:
	_instance = None
	_lock = Lock()

	def __new__(cls, *args, **kwargs) -> "IMAPConnectionPool":
		with cls._lock:
			if cls._instance is None:
				cls._instance = super().__new__(cls)
				cls._instance._pools = {}
				cls._instance._pool_lock = Lock()
				cls._instance._running = False
		return cls._instance

	def __init__(self) -> None:
		if hasattr(self, "_initialized"):
			return

		imap_limits = get_imap_limits()
		self.max_connections = imap_limits["max_connections"]
		self.authenticated_timeout = imap_limits["authenticated_timeout"]
		self.unauthenticated_timeout = imap_limits["unauthenticated_timeout"]
		self.idle_timeout = imap_limits["idle_timeout"]
		self.cleanup_interval = imap_limits["cleanup_interval"]

		self._initialized = True
		self._running = True
		self._cleanup_thread = None
		self._initialize_cleanup_thread()

	def get_connection(
		self, host: str, port: int, username: str, password: str, use_ssl: bool
	) -> "IMAPConnection":
		key = (host, port, username)
		with self._pool_lock:
			if key not in self._pools:
				self._pools[key] = Queue(self.max_connections)
				self._running = True
				self._initialize_cleanup_thread()

		pool = self._pools[key]

		with Lock():
			while not pool.empty():
				connection: IMAPConnection = pool.get()
				if connection.is_valid():
					connection.last_used = time.time()
					connection.idle_since = None
					return connection
				else:
					connection.close()

			if pool.qsize() < self.max_connections:
				return IMAPConnection(
					host,
					port,
					username,
					password,
					use_ssl,
					self.authenticated_timeout,
					self.unauthenticated_timeout,
					self.idle_timeout,
				)

			raise IMAPConnectionLimitError(
				f"IMAP connection pool limit ({self.max_connections}) reached for {key}"
			)

	def return_connection(self, connection: IMAPConnection) -> None:
		key = (connection.host, connection.port, connection.username)
		with self._pool_lock:
			if key in self._pools:
				pool = self._pools[key]
				with Lock():
					if connection.is_active() and pool.qsize() < pool.maxsize:
						connection.last_used = time.time()
						pool.put(connection)
						return
		connection.close()

	def close_all_connections(self) -> None:
		with self._pool_lock:
			for pool in list(self._pools.values()):
				while not pool.empty():
					connection: IMAPConnection = pool.get()
					connection.close()
			self._pools.clear()
			self._running = False
			self._stop_cleanup_thread()

	def _initialize_cleanup_thread(self) -> None:
		if self._running and self._cleanup_thread is None:
			self._cleanup_thread = Thread(target=self._cleanup_stale_connections, daemon=True)
			self._cleanup_thread.start()

	def _cleanup_stale_connections(self) -> None:
		while self._running:
			time.sleep(self.cleanup_interval)
			with self._pool_lock:
				for key, pool in self._pools.items():
					valid_connections = Queue(self.max_connections)
					while not pool.empty():
						connection: IMAPConnection = pool.get()
						if connection.is_valid():
							valid_connections.put(connection)
						else:
							connection.close()
					self._pools[key] = valid_connections

	def _stop_cleanup_thread(self) -> None:
		if self._cleanup_thread and self._cleanup_thread.is_alive():
			self._cleanup_thread.join()
			self._cleanup_thread = None


class IMAPContext:
	def __init__(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool = False,
	) -> None:
		self._pool = IMAPConnectionPool()
		self._host = host
		self._port = port
		self._username = username
		self._password = password
		self._use_ssl = use_ssl
		self._connection = None

	def __enter__(self) -> IMAP4 | IMAP4_SSL:
		self._connection: IMAPConnection = self._pool.get_connection(
			self._host,
			self._port,
			self._username,
			self._password,
			self._use_ssl,
		)
		return self._connection.session

	def __exit__(self, exc_type, exc_value, traceback) -> None:
		if exc_type is not None:
			self._connection.close()
		else:
			self._pool.return_connection(self._connection)


@contextmanager
def imap_server(
	host: str,
	port: int,
	username: str,
	password: str,
	use_ssl: bool = False,
) -> Generator[IMAP4 | IMAP4_SSL, None, None]:
	_pool = IMAPConnectionPool()
	_connection: IMAPConnection = _pool.get_connection(host, port, username, password, use_ssl)

	try:
		yield _connection.session
	finally:
		if _connection:
			_pool.return_connection(_connection)
