import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import SpamNumber, SpamNumberStore

logger = logging.getLogger(__name__)


class BaseExporter:
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, store: SpamNumberStore, filename: str) -> Path:
        raise NotImplementedError


class TxtExporter(BaseExporter):
    def save(self, store: SpamNumberStore, filename: str) -> Path:
        filepath = self.output_dir / filename
        numbers = sorted(store.get_numbers_only())

        with open(filepath, "w", encoding="utf-8") as f:
            for num in numbers:
                f.write(f"{num}\n")

        logger.info(f"Saved {len(numbers)} numbers to {filepath}")
        return filepath


class DialerExporter(BaseExporter):
    def save(self, store: SpamNumberStore, filename: str) -> Path:
        filepath = self.output_dir / filename
        numbers = sorted(store.get_numbers_only())

        with open(filepath, "w", encoding="utf-8") as f:
            for num in numbers:
                f.write(f"+34{num}\n")

        logger.info(f"Saved {len(numbers)} numbers to {filepath}")
        return filepath


class VcfExporter(BaseExporter):
    def save(
        self, store: SpamNumberStore, filename: str, contact_name: str = "Spam"
    ) -> Path:
        filepath = self.output_dir / filename
        numbers = sorted(store.get_numbers_only())

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")
            f.write(f"FN:{contact_name}\n")
            f.write(f"FN;CHARSET=UTF-8:{contact_name}\n")

            for i, num in enumerate(numbers, 1):
                f.write(f"TEL;TYPE=CELL:+34{num}\n")

            f.write("END:VCARD\n")

        logger.info(f"Saved {len(numbers)} numbers to {filepath}")
        return filepath


class JsonExporter(BaseExporter):
    def save(self, store: SpamNumberStore, filename: str) -> Path:
        filepath = self.output_dir / filename
        spam_numbers = store.get_all()

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_count": len(spam_numbers),
            "numbers": [
                {
                    "phone_number": num.phone_number,
                    "source": num.source,
                    "first_seen": num.first_seen.isoformat(),
                    "last_seen": num.last_seen.isoformat(),
                    "spam_type": num.spam_type.value,
                    "reports": num.reports,
                    "metadata": num.metadata,
                }
                for num in spam_numbers
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(spam_numbers)} numbers to {filepath}")
        return filepath


class ExporterFactory:
    @staticmethod
    def create_exporter(
        exporter_type: str, output_dir: str = "."
    ) -> Optional[BaseExporter]:
        exporters = {
            "txt": TxtExporter,
            "dialer": DialerExporter,
            "vcf": VcfExporter,
            "json": JsonExporter,
        }

        exporter_class = exporters.get(exporter_type)
        if exporter_class:
            return exporter_class(output_dir)
        return None


class MultiExporter:
    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        self.exporters: dict[str, BaseExporter] = {}

    def register(self, name: str, exporter: BaseExporter):
        self.exporters[name] = exporter

    def export_all(self, store: SpamNumberStore, config: dict) -> dict[str, Path]:
        results = {}

        if "base_file" in config:
            txt_exporter = self.exporters.get("txt") or TxtExporter(self.output_dir)
            results["txt"] = txt_exporter.save(store, config["base_file"])

        if "dialer_file" in config:
            dialer_exporter = self.exporters.get("dialer") or DialerExporter(
                self.output_dir
            )
            results["dialer"] = dialer_exporter.save(store, config["dialer_file"])

        if "vcf_file" in config:
            vcf_exporter = self.exporters.get("vcf") or VcfExporter(self.output_dir)
            contact_name = config.get("vcf_contact_name", "Spam")
            results["vcf"] = vcf_exporter.save(store, config["vcf_file"], contact_name)

        if "json_file" in config:
            json_exporter = self.exporters.get("json") or JsonExporter(self.output_dir)
            results["json"] = json_exporter.save(store, config["json_file"])

        return results
