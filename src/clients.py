import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .http_client import HttpClient
from .models import NumberValidator

logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    url: str
    enabled: bool = True
    params: dict | None = None
    use_tls: bool = False


class BaseSourceClient(ABC):
    def __init__(self, http_client: HttpClient, source_name: str):
        self.http_client = http_client
        self.source_name = source_name

    @abstractmethod
    async def fetch_numbers(self) -> set[str]:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    async def fetch_content(self) -> str:
        try:
            return await self.http_client.fetch(self.url)
        except Exception as e:
            logger.error(f"Error fetching from {self.source_name}: {e}")
            return ""


class SpamCallsClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://spamcalls.net/es/country-code/34"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_with_prefix(content)


class TellowsClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://www.tellows.es/stats"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_with_prefix(content)


class CleverDialerClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://www.cleverdialer.es/top-spammer-de-las-ultimas-24-horas"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_generic(content)


class TelefonoSpamClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://www.telefonospam.com/ultimos"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_generic(content)


class DetectaSpamClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://detectaspam.com/"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_generic(content)


class SlicklyClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://slick.ly/es"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_generic(content)


class DatosTelefonicosClient(BaseSourceClient):
    def __init__(self, http_client: HttpClient, source_name: str, endpoint: str):
        super().__init__(http_client, source_name)
        self.endpoint = endpoint

    @property
    def url(self) -> str:
        return f"https://datostelefonicos.com/{self.endpoint}"

    async def fetch_numbers(self, limit: int = 200) -> set[str]:
        content = await self.http_client.fetch(self.url, params={"limit": limit})
        if not content:
            return set()
        return NumberValidator.extract_numbers_generic(content)


class OpenSpamClient(BaseSourceClient):
    @property
    def url(self) -> str:
        return "https://openspam.es/"

    async def fetch_numbers(self) -> set[str]:
        content = await self.fetch_content()
        if not content:
            return set()
        return NumberValidator.extract_numbers_with_prefix(content)


class NumeroSpamClient(BaseSourceClient):
    PREFIXES = {
        "provincias": [
            "almeria",
            "huelva",
            "cadiz",
            "jaen",
            "cordoba",
            "malaga",
            "granada",
            "sevilla",
            "huesca",
            "teruel",
            "zaragoza",
            "asturias",
            "islas-baleares",
            "las-palmas",
            "santa-cruz-de-tenerife",
            "cantabria",
            "albacete",
            "ciudad-real",
            "cuenca",
            "guadalajara",
            "toledo",
            "avila",
            "burgos",
            "leon",
            "palencia",
            "salamanca",
            "segovia",
            "soria",
            "valladolid",
            "zamora",
            "barcelona",
            "girona",
            "lleida",
            "tarragona",
            "alicante",
            "castellon",
            "valencia",
            "badajoz",
            "caceres",
            "a-coruna",
            "lugo",
            "orense",
            "pontevedra",
            "alava",
            "vizcaya",
            "guipuzcoa",
            "la-rioja",
            "murcia",
            "madrid",
            "navarra",
        ],
        "especiales": [
            "704",
            "800",
            "803",
            "806",
            "807",
            "900",
            "901",
            "902",
            "903",
            "905",
            "906",
            "907",
            "908",
            "909",
        ],
        "moviles": [
            "606",
            "608",
            "609",
            "616",
            "618",
            "619",
            "620",
            "626",
            "628",
            "629",
            "630",
            "636",
            "638",
            "639",
            "646",
            "648",
            "649",
            "650",
            "659",
            "660",
            "669",
            "676",
            "679",
            "680",
            "681",
            "682",
            "683",
            "686",
            "689",
            "690",
            "696",
            "699",
            "717",
            "600",
            "603",
            "607",
            "610",
            "617",
            "627",
            "634",
            "637",
            "647",
            "661",
            "662",
            "663",
            "664",
            "666",
            "667",
            "670",
            "671",
            "672",
            "673",
            "674",
            "677",
            "678",
            "687",
            "697",
            "711",
            "727",
            "605",
            "615",
            "625",
            "635",
            "645",
            "651",
            "652",
            "653",
            "654",
            "655",
            "656",
            "657",
            "658",
            "665",
            "675",
            "685",
            "691",
            "692",
            "747",
            "748",
            "612",
            "631",
            "632",
            "613",
            "622",
            "623",
            "633",
            "712",
            "722",
            "624",
            "641",
            "642",
            "643",
            "693",
            "694",
            "695",
            "601",
            "604",
            "640",
            "611",
            "698",
            "621",
            "644",
            "668",
            "688",
            "684",
            "602",
            "744",
        ],
    }

    def __init__(self, http_client: HttpClient, base_url: str = "https://numerospam.es"):
        super().__init__(http_client, "numerospam")
        self.base_url = base_url

    @property
    def url(self) -> str:
        return self.base_url

    async def fetch_all_prefixes(self) -> set[str]:
        import asyncio

        all_numbers = set()

        tasks = []
        for provincia in self.PREFIXES["provincias"]:
            tasks.append(self._fetch_prefix(f"/prefijos/es/{provincia}"))

        for especial in self.PREFIXES["especiales"]:
            tasks.append(self._fetch_prefix(f"/prefijos-especiales/es/{especial}"))

        for movil in self.PREFIXES["moviles"]:
            tasks.append(self._fetch_prefix(f"/moviles/es/{movil}"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, set):
                all_numbers.update(result)
            elif isinstance(result, Exception):
                logger.error(f"Error fetching prefix: {result}")

        return all_numbers

    async def _fetch_prefix(self, path: str) -> set[str]:
        url = f"{self.base_url}{path}"
        try:
            content = await self.http_client.fetch(url)
            if content:
                return NumberValidator.extract_numbers_generic(content)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return set()

    async def fetch_numbers(self) -> set[str]:
        return await self.fetch_all_prefixes()


class SourceClientFactory:
    @staticmethod
    def create_client(client_type: str, http_client: HttpClient) -> "BaseSourceClient | None":
        if client_type == "spamcalls":
            return SpamCallsClient(http_client, "spamcalls")
        if client_type == "tellows":
            return TellowsClient(http_client, "tellows")
        if client_type == "cleverdialer":
            return CleverDialerClient(http_client, "cleverdialer")
        if client_type == "telefonospam":
            return TelefonoSpamClient(http_client, "telefonospam")
        if client_type == "detectaspam":
            return DetectaSpamClient(http_client, "detectaspam")
        if client_type == "slickly":
            return SlicklyClient(http_client, "slickly")
        if client_type == "datostelefonicos_last":
            return DatosTelefonicosClient(
                http_client, "datostelefonicos_last", "ultimos-buscados/es"
            )
        if client_type == "datostelefonicos_top":
            return DatosTelefonicosClient(http_client, "datostelefonicos_top", "mas-buscados/es")
        if client_type == "openspam":
            return OpenSpamClient(http_client, "openspam")
        if client_type == "numerospam":
            return NumeroSpamClient(http_client)
        return None
