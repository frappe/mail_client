from abc import ABC, abstractmethod
from typing import Literal

import digitalocean


class BaseDNSProvider(ABC):
	"""An abstract base class for DNS providers."""

	@abstractmethod
	def create_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Creates a DNS record."""
		pass

	@abstractmethod
	def read_dns_records(self, domain: str) -> list:
		"""Reads DNS records for a domain."""
		pass

	@abstractmethod
	def update_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Updates a DNS record."""
		pass

	@abstractmethod
	def delete_dns_record(self, domain: str, type: str, host: str) -> bool:
		"""Deletes a DNS record."""
		pass


class DigitalOceanDNS(BaseDNSProvider):
	"""A DNS provider for DigitalOcean."""

	def __init__(self, token: str) -> None:
		"""Initializes the DigitalOceanDNS provider."""

		self.token = token

	def create_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Creates a DNS record."""

		record = (
			digitalocean.Domain(token=self.token, name=domain)
			.create_new_domain_record(type=type, name=host, data=value, priority=priority, ttl=ttl)
			.get("domain_record", {})
		)
		return bool(record.get("id"))

	def read_dns_records(self, domain: str) -> list:
		"""Reads DNS records for a domain."""

		return digitalocean.Domain(token=self.token, name=domain).get_records()

	def update_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Updates a DNS record."""

		records = self.read_dns_records(domain)
		for record in records:
			if record.name == host and record.type == type:
				if record.data == value:
					return True

				record.data = value
				record.priority = priority
				record.ttl = ttl
				record.save()

				return True

		return False

	def delete_dns_record(self, domain: str, type: str, host: str) -> bool:
		"""Deletes a DNS record."""

		records = self.read_dns_records(domain)

		if not records:
			return True

		for record in records:
			if record.name == host and record.type == type:
				record.destroy()
				return True

		return False


class DNSProvider:
	"""A DNS provider class that uses a specific DNS provider."""

	def __init__(self, provider: Literal["DigitalOcean"], token: str) -> None:
		"""Initializes the DNS provider with the specified provider and token."""

		self.provider = self._get_dns_provider(provider, token)

	def _get_dns_provider(self, provider: str, token: str) -> BaseDNSProvider:
		"""Returns the DNS provider based on the provider name."""

		if provider == "DigitalOcean":
			return DigitalOceanDNS(token=token)
		else:
			raise ValueError(f"Unsupported DNS Provider: {provider}")

	def create_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Creates a DNS record."""

		return self.provider.create_dns_record(domain, type, host, value, ttl, priority)

	def read_dns_records(self, domain: str) -> list:
		"""Reads DNS records for a domain."""

		return self.provider.read_dns_records(domain)

	def update_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Updates a DNS record."""

		return self.provider.update_dns_record(domain, type, host, value, ttl, priority)

	def delete_dns_record(self, domain: str, type: str, host: str) -> bool:
		"""Deletes a DNS record."""

		return self.provider.delete_dns_record(domain, type, host)

	def create_or_update_dns_record(
		self, domain: str, type: str, host: str, value: str, ttl: int, priority: int = 0
	) -> bool:
		"""Creates or updates a DNS record based on the existence of the record."""

		return self.update_dns_record(domain, type, host, value, ttl, priority) or self.create_dns_record(
			domain, type, host, value, ttl, priority
		)
