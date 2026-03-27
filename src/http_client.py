import os
import logging
import asyncio
from typing import Optional
from dataclasses import dataclass

import aiohttp
import requests

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    backoff_base: float = 1.0


class HttpClient:
    def __init__(
        self,
        timeout: int = 10,
        retry_config: Optional[RetryConfig] = None,
        proxy_url: Optional[str] = None,
    ):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_config = retry_config or RetryConfig()
        self.proxy_url = proxy_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def fetch(
        self,
        url: str,
        use_tls_client: bool = False,
        params: Optional[dict] = None,
    ) -> str:
        for attempt in range(self.retry_config.max_attempts):
            try:
                if use_tls_client:
                    return await self._fetch_with_tls(url, params)
                return await self._fetch_async(url, params)
            except Exception as e:
                if attempt == self.retry_config.max_attempts - 1:
                    logger.error(
                        f"Failed to fetch {url} after {self.retry_config.max_attempts} attempts: {e}"
                    )
                    raise
                wait_time = self.retry_config.backoff_base * (
                    self.retry_config.backoff_factor**attempt
                )
                logger.warning(
                    f"Attempt {attempt + 1} failed for {url}, retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)
        return ""

    async def _fetch_async(self, url: str, params: Optional[dict] = None) -> str:
        session = await self._get_session()
        async with session.get(url, params=params, proxy=self.proxy_url) as response:
            response.raise_for_status()
            return await response.text()

    async def _fetch_with_tls(self, url: str, params: Optional[dict] = None) -> str:
        session = await self._get_session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with session.get(
            url, params=params, proxy=self.proxy_url, headers=headers
        ) as response:
            response.raise_for_status()
            return await response.text()

    def fetch_sync(self, url: str, use_tls_client: bool = False) -> str:
        proxies = (
            {"http": self.proxy_url, "https": self.proxy_url}
            if self.proxy_url
            else None
        )
        for attempt in range(self.retry_config.max_attempts):
            try:
                if use_tls_client:
                    import tls_client

                    session = tls_client.Session(
                        client_identifier="chrome_120", random_tls_extension_order=True
                    )
                    if self.proxy_url:
                        session.proxies = proxies
                    response = session.get(url)
                    response.raise_for_status()
                    return response.text
                response = requests.get(
                    url, proxies=proxies, timeout=self.timeout.total
                )
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == self.retry_config.max_attempts - 1:
                    logger.error(
                        f"Failed to fetch {url} after {self.retry_config.max_attempts} attempts: {e}"
                    )
                    raise
                wait_time = self.retry_config.backoff_base * (
                    self.retry_config.backoff_factor**attempt
                )
                logger.warning(
                    f"Attempt {attempt + 1} failed for {url}, retrying in {wait_time}s: {e}"
                )
                import time

                time.sleep(wait_time)
        return ""

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
