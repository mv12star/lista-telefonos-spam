import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import NumberValidator, SpamNumber, SpamNumberStore


class TestNumberValidator:
    def test_normalize_number_with_plus34(self):
        assert NumberValidator.normalize_number("+34600000000") == "600000000"
        assert NumberValidator.normalize_number("+34 600 000 000") == "600000000"

    def test_normalize_number_with_34_prefix(self):
        assert NumberValidator.normalize_number("34600000000") == "600000000"

    def test_normalize_number_without_prefix(self):
        assert NumberValidator.normalize_number("600000000") == "600000000"
        assert NumberValidator.normalize_number("600 000 000") == "600000000"

    def test_normalize_number_invalid(self):
        assert NumberValidator.normalize_number("123456789") is None
        assert NumberValidator.normalize_number("+123456789") is None

    def test_is_valid_spanish_number_mobile(self):
        assert NumberValidator.is_valid_spanish_number("600000000") is True
        assert NumberValidator.is_valid_spanish_number("700000000") is True
        assert NumberValidator.is_valid_spanish_number("800000000") is True
        assert NumberValidator.is_valid_spanish_number("900000000") is True

    def test_is_valid_spanish_number_invalid(self):
        assert NumberValidator.is_valid_spanish_number("500000000") is False
        assert NumberValidator.is_valid_spanish_number("123456789") is False
        assert NumberValidator.is_valid_spanish_number("60000000") is False
        assert NumberValidator.is_valid_spanish_number("6000000000") is False

    def test_extract_numbers_with_prefix(self):
        content = """
        Spam number: +34600000000
        Another: 34600000001
        Another one: +34600000002
        Invalid: +123456789
        """
        numbers = NumberValidator.extract_numbers_with_prefix(content)
        assert "600000000" in numbers
        assert "600000001" in numbers
        assert "600000002" in numbers

    def test_extract_numbers_generic(self):
        content = """
        Spam: 600000000
        Another: 700000000
        Invalid: 500000000
        Short: 123456
        """
        numbers = NumberValidator.extract_numbers_generic(content)
        assert "600000000" in numbers
        assert "700000000" in numbers
        assert "500000000" not in numbers
        assert "123456" not in numbers

    def test_validate_and_filter(self):
        numbers = {"600000000", "700000000", "500000000", "123456789", "60000000"}
        filtered = NumberValidator.validate_and_filter(numbers)
        assert "600000000" in filtered
        assert "700000000" in filtered
        assert "500000000" not in filtered
        assert "123456789" not in filtered
        assert "60000000" not in filtered


class TestSpamNumberStore:
    def test_add_number(self):
        store = SpamNumberStore()
        spam_num = store.add("600000000", "test_source")

        assert spam_num.phone_number == "600000000"
        assert spam_num.source == "test_source"
        assert spam_num.reports == 1

    def test_add_duplicate_number_increments_reports(self):
        store = SpamNumberStore()
        store.add("600000000", "source1")
        store.add("600000000", "source2")

        assert len(store) == 1
        numbers = store.get_numbers_only()
        assert "600000000" in numbers

    def test_add_invalid_number_raises_error(self):
        store = SpamNumberStore()

        with pytest.raises(ValueError):
            store.add("123456789", "test")

    def test_add_batch(self):
        store = SpamNumberStore()
        numbers = {"600000000", "700000000", "800000000", "123456789"}

        count = store.add_batch(numbers, "test_source")

        assert count == 3
        assert len(store) == 3

    def test_merge_stores(self):
        store1 = SpamNumberStore()
        store1.add("600000000", "source1")

        store2 = SpamNumberStore()
        store2.add("600000000", "source2")
        store2.add("700000000", "source2")

        count = store1.merge(store2)

        assert count == 2
        assert len(store1) == 2

    def test_get_all_returns_spam_numbers(self):
        store = SpamNumberStore()
        store.add("600000000", "test", {"meta": "data"})

        all_numbers = store.get_all()

        assert len(all_numbers) == 1
        assert isinstance(all_numbers[0], SpamNumber)
        assert all_numbers[0].metadata["meta"] == "data"


class TestSpamNumber:
    def test_spam_number_equality(self):
        num1 = SpamNumber(phone_number="600000000", source="test")
        num2 = SpamNumber(phone_number="600000000", source="other")

        assert num1 == num2

    def test_spam_number_hash(self):
        num1 = SpamNumber(phone_number="600000000", source="test")
        num2 = SpamNumber(phone_number="600000000", source="other")

        assert hash(num1) == hash(num2)
        assert len({num1, num2}) == 1
