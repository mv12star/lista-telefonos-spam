import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exporter import DialerExporter, JsonExporter, TxtExporter, VcfExporter
from src.models import SpamNumberStore


class TestTxtExporter:
    def test_save_writes_numbers(self):
        store = SpamNumberStore()
        store.add("600000000", "test")
        store.add("700000000", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = TxtExporter(tmpdir)
            filepath = exporter.save(store, "test.txt")

            assert filepath.exists()
            content = filepath.read_text()
            assert "600000000" in content
            assert "700000000" in content

    def test_save_sorts_numbers(self):
        store = SpamNumberStore()
        store.add("700000000", "test")
        store.add("600000000", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = TxtExporter(tmpdir)
            filepath = exporter.save(store, "test.txt")

            content = filepath.read_text()
            lines = content.strip().split("\n")
            assert lines[0] == "600000000"
            assert lines[1] == "700000000"


class TestDialerExporter:
    def test_save_adds_plus34_prefix(self):
        store = SpamNumberStore()
        store.add("600000000", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = DialerExporter(tmpdir)
            filepath = exporter.save(store, "dialer.txt")

            content = filepath.read_text()
            assert "+34600000000" in content


class TestVcfExporter:
    def test_save_creates_valid_vcf(self):
        store = SpamNumberStore()
        store.add("600000000", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = VcfExporter(tmpdir)
            filepath = exporter.save(store, "contacts.vcf", "Spam")

            assert filepath.exists()
            content = filepath.read_text()
            assert "BEGIN:VCARD" in content
            assert "VERSION:3.0" in content
            assert "FN:Spam" in content
            assert "TEL;TYPE=CELL:+34600000000" in content
            assert "END:VCARD" in content


class TestJsonExporter:
    def test_save_creates_json_with_metadata(self):
        store = SpamNumberStore()
        store.add("600000000", "test", {"spam_type": "telemarketing"})

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JsonExporter(tmpdir)
            filepath = exporter.save(store, "spam.json")

            assert filepath.exists()
            with open(filepath) as f:
                data = json.load(f)

            assert "generated_at" in data
            assert data["total_count"] == 1
            assert len(data["numbers"]) == 1
            assert data["numbers"][0]["phone_number"] == "600000000"
            assert data["numbers"][0]["source"] == "test"
