import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SpamType(Enum):
    UNKNOWN = "unknown"
    TELEMARKETING = "telemarketing"
    SCAM = "scam"
    SURVEY = "survey"
    DEBT_COLLECTION = "debt_collection"


@dataclass
class SpamNumber:
    phone_number: str
    source: str
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    spam_type: SpamType = SpamType.UNKNOWN
    reports: int = 1
    metadata: dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.phone_number)

    def __eq__(self, other):
        if isinstance(other, SpamNumber):
            return self.phone_number == other.phone_number
        return False


class NumberValidator:
    SPANISH_MOBILE_PREFIXES = ("6", "7", "8", "9")
    SPANISH_SPECIAL_PREFIXES = (
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
    )

    @staticmethod
    def normalize_number(number: str) -> str | None:
        cleaned = re.sub(r"[^\d+]", "", number)

        if cleaned.startswith("+34") and len(cleaned[3:]) == 9:
            return cleaned[3:]
        if cleaned.startswith("34") and len(cleaned[2:]) == 9:
            return cleaned[2:]
        if len(cleaned) == 9 and cleaned[0] in "346789":
            return cleaned

        return None

    @staticmethod
    def is_valid_spanish_number(number: str) -> bool:
        normalized = NumberValidator.normalize_number(number)
        if not normalized or len(normalized) != 9:
            return False
        return normalized[0] in NumberValidator.SPANISH_MOBILE_PREFIXES

    @staticmethod
    def extract_numbers_with_prefix(content: str) -> set[str]:
        numbers = set()
        patterns = re.findall(r"[+346789]\d{8,11}", content)

        for num in patterns:
            normalized = NumberValidator.normalize_number(num)
            if normalized:
                numbers.add(normalized)

        return numbers

    @staticmethod
    def extract_numbers_generic(content: str) -> set[str]:
        numbers = set()
        patterns = re.findall(r"[6789]\d{8}", content)

        for num in patterns:
            if NumberValidator.is_valid_spanish_number(num):
                numbers.add(num)

        return numbers

    @staticmethod
    def validate_and_filter(numbers: set[str]) -> set[str]:
        return {num for num in numbers if NumberValidator.is_valid_spanish_number(num)}


class SpamNumberStore:
    def __init__(self):
        self._numbers: dict[str, SpamNumber] = {}

    def add(self, phone_number: str, source: str, metadata: dict | None = None) -> SpamNumber:
        normalized = NumberValidator.normalize_number(phone_number)
        if not normalized or not NumberValidator.is_valid_spanish_number(normalized):
            raise ValueError(f"Invalid Spanish phone number: {phone_number}")

        if normalized in self._numbers:
            existing = self._numbers[normalized]
            existing.last_seen = datetime.now()
            existing.reports += 1
            if source not in existing.metadata.get("sources", []):
                existing.metadata.setdefault("sources", []).append(source)
            if metadata:
                existing.metadata.update(metadata)
            return existing

        spam_number = SpamNumber(phone_number=normalized, source=source, metadata=metadata or {})
        self._numbers[normalized] = spam_number
        return spam_number

    def add_batch(self, numbers: set[str], source: str) -> int:
        count = 0
        for num in numbers:
            try:
                self.add(num, source)
                count += 1
            except ValueError:
                continue
        return count

    def get_all(self) -> list[SpamNumber]:
        return list(self._numbers.values())

    def get_numbers_only(self) -> set[str]:
        return set(self._numbers.keys())

    def merge(self, other: "SpamNumberStore") -> int:
        count = 0
        for spam_number in other.get_all():
            try:
                self.add(spam_number.phone_number, spam_number.source, spam_number.metadata)
                count += 1
            except ValueError:
                continue
        return count

    def __len__(self) -> int:
        return len(self._numbers)
