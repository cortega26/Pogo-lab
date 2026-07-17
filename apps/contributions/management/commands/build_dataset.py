from django.core.management.base import BaseCommand

from apps.contributions.services import build_dataset_version


class Command(BaseCommand):
    help = "Construye una nueva versión del dataset comunitario (idempotente: mismo input → mismo checksum)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-sample",
            type=int,
            default=30,
            help="Mínimo de observaciones requerido (default: 30).",
        )
        parser.add_argument(
            "--pipeline-version",
            type=str,
            default="1.0.0",
            help="Versión del pipeline (default: 1.0.0).",
        )

    def handle(self, **options):
        min_sample = options["min_sample"]
        pipeline_version = options["pipeline_version"]

        version = build_dataset_version(
            criteria={"min_sample": min_sample, "state_filter": "valid"},
            pipeline_version=pipeline_version,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dataset v{version.number} construido: "
                f"{version.row_count} filas, "
                f"min_sample_met={version.min_sample_met}, "
                f"checksum={version.checksum}"
            )
        )
