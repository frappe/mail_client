import time
from collections.abc import Generator
from contextlib import contextmanager, suppress
from queue import Queue
from smtplib import SMTP, SMTP_SSL, SMTPServerDisconnected
from threading import Lock, Thread

from mail.utils.cache import get_smtp_limits


class SMTPConnectionLimitError(Exception):
	pass


class SMTPConnection:
	def __init__(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool,
		use_tls: bool,
		inactivity_timeout: int,
		session_duration: int,
		max_messages: int,
	) -> None:
		self.__created_at = time.time()
		self.__inactivity_timeout = inactivity_timeout
		self.__session_duration = session_duration
		self.__max_messages = max_messages
		self.__email_count = 0
		self.__session = self.create_session(host, port, username, password, use_ssl, use_tls)

		self.host = host
		self.port = port
		self.username = username
		self.last_used = time.time()

	@property
	def session(self) -> SMTP | SMTP_SSL:
		return self.__session

	def _is_session_active(self) -> bool:
		if not self.session:
			return False

		if not hasattr(self, "_last_check") or (time.time() - self._last_check) > 10:
			self._last_check = time.time()
			try:
				return self.session.noop()[0] == 250
			except Exception:
				return False

		return True

	def is_session_valid(self) -> bool:
		current_time = time.time()
		expired = (
			current_time - self.last_used > self.__inactivity_timeout
			or current_time - self.__created_at > self.__session_duration
			or self.__email_count >= self.__max_messages
		)
		return not expired and self._is_session_active()

	def increment_email_count(self) -> None:
		self.__email_count += 1
		self.last_used = time.time()

	def close(self) -> None:
		if self.session:
			with suppress(SMTPServerDisconnected, TimeoutError, OSError):
				self.session.quit()

	@classmethod
	def create_session(
		cls, host: str, port: int, username: str, password: str, use_ssl: bool, use_tls: bool
	) -> SMTP | SMTP_SSL:
		_SMTP = SMTP_SSL if use_ssl else SMTP
		session = _SMTP(host, port)
		if use_tls:
			session.starttls()
		session.login(username, password)
		return session


class SMTPConnectionPool:
	_instance = None
	_lock = Lock()

	def __new__(cls, *args, **kwargs) -> "SMTPConnectionPool":
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

		smtp_limits = get_smtp_limits()
		self.max_connections = smtp_limits["max_connections"]
		self.max_messages = smtp_limits["max_messages"]
		self.session_duration = smtp_limits["session_duration"]
		self.inactivity_timeout = smtp_limits["inactivity_timeout"]
		self.cleanup_interval = smtp_limits["cleanup_interval"]

		self._initialized = True
		self._running = True
		self._cleanup_thread = None
		self._initialize_cleanup_thread()

	def get_connection(
		self,
		host: str,
		port: int,
		username: str,
		password: str,
		use_ssl: bool,
		use_tls: bool,
	) -> "SMTPConnection":
		key = (host, port, username)
		with self._pool_lock:
			if key not in self._pools:
				self._pools[key] = Queue(self.max_connections)
				self._running = True
				self._initialize_cleanup_thread()

			pool = self._pools[key]
			while not pool.empty():
				connection: SMTPConnection = pool.get()
				if connection.is_session_valid():
					connection.last_used = time.time()
					return connection
				connection.close()

			if pool.qsize() < self.max_connections:
				return SMTPConnection(
					host,
					port,
					username,
					password,
					use_ssl,
					use_tls,
					self.inactivity_timeout,
					self.session_duration,
					self.max_messages,
				)

		raise SMTPConnectionLimitError(
			f"SMTP connection pool limit ({self.max_connections}) reached for {key}"
		)

	def return_connection(self, connection: SMTPConnection) -> None:
		key = (connection.host, connection.port, connection.username)
		with self._pool_lock:
			if key in self._pools:
				pool = self._pools[key]
				if connection.is_session_valid() and not pool.full():
					pool.put(connection)
					return
		connection.close()

	def close_all_connections(self) -> None:
		with self._pool_lock:
			for pool in list(self._pools.values()):
				while not pool.empty():
					connection: SMTPConnection = pool.get()
					connection.close()
			self._pools.clear()
			self._running = False
			self._stop_cleanup_thread()

	def _initialize_cleanup_thread(self) -> None:
		if self._running and (not self._cleanup_thread or not self._cleanup_thread.is_alive()):
			self._cleanup_thread = Thread(target=self._cleanup_stale_connections, daemon=True)
			self._cleanup_thread.start()

	def _cleanup_stale_connections(self) -> None:
		while self._running:
			time.sleep(self.cleanup_interval)
			with self._pool_lock:
				for key, pool in self._pools.items():
					valid_connections = Queue(self.max_connections)
					while not pool.empty():
						connection: SMTPConnection = pool.get()
						if connection.is_session_valid():
							valid_connections.put(connection)
						else:
							connection.close()
					self._pools[key] = valid_connections

	def _stop_cleanup_thread(self) -> None:
		if self._cleanup_thread and self._cleanup_thread.is_alive():
			self._cleanup_thread.join()
			self._cleanup_thread = None


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
		self._connection: SMTPConnection = self._pool.get_connection(
			self._host,
			self._port,
			self._username,
			self._password,
			self._use_ssl,
			self._use_tls,
		)
		return self._connection.session

	def __exit__(self, exc_type, exc_value, traceback) -> None:
		if exc_type is not None:
			self._connection.close()
		else:
			self._connection.increment_email_count()
			self._pool.return_connection(self._connection)


@contextmanager
def smtp_server(
	host: str,
	port: int,
	username: str,
	password: str,
	use_ssl: bool = False,
	use_tls: bool = False,
) -> Generator[SMTP | SMTP_SSL, None, None]:
	_pool = SMTPConnectionPool()
	_connection: SMTPConnection = _pool.get_connection(host, port, username, password, use_ssl, use_tls)

	try:
		yield _connection.session
	finally:
		if _connection:
			_connection.increment_email_count()
			_pool.return_connection(_connection)
