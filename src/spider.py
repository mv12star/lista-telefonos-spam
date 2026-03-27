import asyncio
import logging
import os
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import yaml

from .http_client import HttpClient, RetryConfig
from .clients import SourceClientFactory, BaseSourceClient
from .models import SpamNumberStore, NumberValidator
from .exporter import MultiExporter, ExporterFactory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SpamSpider:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: dict = {}
        self.http_client: Optional[HttpClient] = None
        self.store = SpamNumberStore()
        self._load_config()

    def _load_config(self):
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            self.config = self._get_default_config()
            return

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def _get_default_config(self) -> dict:
        return {
            "scraper": {
                "timeout": 10,
                "max_workers": 10,
                "retry": {"max_attempts": 3, "backoff_factor": 2, "backoff_base": 1},
                "proxy": {"enabled": False, "url": ""},
            },
            "sources": {},
            "output": {
                "base_file": "lista_numeros_spam.txt",
                "dialer_file": "numeros_spam_dialer.txt",
                "vcf_file": "contactos_spam.vcf",
                "json_file": "numeros_spam.json",
                "vcf_contact_name": "Spam",
            },
        }

    def _init_http_client(self):
        scraper_config = self.config.get("scraper", {})
        retry_config = RetryConfig(
            max_attempts=scraper_config.get("retry", {}).get("max_attempts", 3),
            backoff_factor=scraper_config.get("retry", {}).get("backoff_factor", 2),
            backoff_base=scraper_config.get("retry", {}).get("backoff_base", 1),
        )

        proxy_url = None
        if scraper_config.get("proxy", {}).get("enabled"):
            proxy_url = scraper_config.get("proxy", {}).get("url", "") or os.getenv(
                "PROXY"
            )

        self.http_client = HttpClient(
            timeout=scraper_config.get("timeout", 10),
            retry_config=retry_config,
            proxy_url=proxy_url,
        )

    async def _fetch_from_source(self, client: BaseSourceClient) -> int:
        try:
            numbers = await client.fetch_numbers()
            valid_numbers = NumberValidator.validate_and_filter(numbers)
            count = self.store.add_batch(valid_numbers, client.source_name)
            logger.info(f"Fetched {count} numbers from {client.source_name}")
            return count
        except Exception as e:
            logger.error(f"Error fetching from {client.source_name}: {e}")
            return 0

    async def _fetch_all_sources(self):
        sources_config = self.config.get("sources", {})

        tasks = []
        for source_name, source_config in sources_config.items():
            if not source_config.get("enabled", True):
                logger.info(f"Skipping disabled source: {source_name}")
                continue

            client = SourceClientFactory.create_client(source_name, self.http_client)
            if client:
                tasks.append(self._fetch_from_source(client))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Source fetch error: {result}")

    def load_existing_numbers(self, filepath: str) -> int:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                numbers = {line.strip() for line in f if line.strip()}

            valid_numbers = NumberValidator.validate_and_filter(numbers)
            count = self.store.add_batch(valid_numbers, "existing")
            logger.info(f"Loaded {count} existing numbers from {filepath}")
            return count
        except FileNotFoundError:
            logger.warning(f"File {filepath} not found, starting fresh")
            return 0

    async def run(self) -> SpamNumberStore:
        logger.info("Starting spam spider...")

        self._init_http_client()

        output_config = self.config.get("output", {})
        base_file = output_config.get("base_file", "lista_numeros_spam.txt")
        self.load_existing_numbers(base_file)

        await self._fetch_all_sources()

        if self.http_client:
            await self.http_client.close()

        logger.info(f"Total unique numbers: {len(self.store)}")
        return self.store

    def export(self, output_dir: str = ".") -> dict:
        output_config = self.config.get("output", {})

        exporter = MultiExporter(output_dir)

        return exporter.export_all(self.store, output_config)

    def run_sync(self) -> dict:
        store = asyncio.run(self.run())
        self.store = store
        return self.export()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Spider de números spam españoles")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to config file"
    )
    parser.add_argument("-o", "--output", default=".", help="Output directory")
    args = parser.parse_args()

    spider = SpamSpider(config_path=args.config)
    results = spider.run_sync()

    print(f"Export completed: {len(results)} files created")
    for name, path in results.items():
        print(f"  - {name}: {path}")


if __name__ == "__main__":
    main()
