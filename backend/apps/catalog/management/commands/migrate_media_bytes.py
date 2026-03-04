"""
Migrate binary media data from SQLite to the active database (PostgreSQL).

Reads media bytes directly from the repo's db.sqlite3 file and updates
the corresponding Media records in the production PostgreSQL database.
This is used after import_full_data --skip-media-bytes to fill in the
binary content without needing a multi-GB JSON export.

Usage (on VPS inside Docker):
    python manage.py migrate_media_bytes
    python manage.py migrate_media_bytes --sqlite-path /app/backend/db.sqlite3
    python manage.py migrate_media_bytes --dry-run
    python manage.py migrate_media_bytes --batch-size 50
"""
import sqlite3
import time
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection

from apps.catalog.models import Media


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_SQLITE = BACKEND_DIR / "db.sqlite3"


class Command(BaseCommand):
    help = "Migrate binary media data from SQLite db.sqlite3 to production DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sqlite-path",
            type=str,
            default=str(DEFAULT_SQLITE),
            help=f"Path to SQLite database (default: {DEFAULT_SQLITE})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview without making changes",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=25,
            help="Records per batch (default: 25)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing bytes (default: skip if bytes exist)",
        )

    def handle(self, *args, **options):
        sqlite_path = Path(options["sqlite_path"])
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        force = options["force"]
        start = time.time()

        if not sqlite_path.exists():
            self.stderr.write(self.style.ERROR(f"SQLite file not found: {sqlite_path}"))
            return

        # Check if we're targeting a different DB (not SQLite itself)
        db_engine = connection.settings_dict.get("ENGINE", "")
        if "sqlite3" in db_engine:
            self.stderr.write(self.style.WARNING(
                "Target DB is also SQLite — this command is meant for SQLite→PostgreSQL migration.\n"
                "If the active DB IS your db.sqlite3 file, you already have the data."
            ))
            return

        self.stdout.write("=" * 60)
        self.stdout.write("  MEDIA BYTES MIGRATION")
        self.stdout.write(f"  Source: {sqlite_path} ({sqlite_path.stat().st_size / 1024 / 1024:.0f} MB)")
        self.stdout.write(f"  Target: {connection.settings_dict.get('NAME', 'unknown')}")
        if dry_run:
            self.stdout.write(self.style.WARNING("  MODE: DRY RUN"))
        self.stdout.write("=" * 60)

        # Connect to source SQLite
        src = sqlite3.connect(str(sqlite_path))
        src.row_factory = sqlite3.Row

        # Get all media filenames from SQLite
        cursor = src.execute(
            "SELECT id, filename, checksum_sha256, size_bytes "
            "FROM catalog_media ORDER BY filename"
        )
        src_records = cursor.fetchall()
        self.stdout.write(f"  Source SQLite: {len(src_records)} media records")

        # Get target media records (filenames that need bytes)
        if force:
            target_media = {m.filename: m for m in Media.objects.only("id", "filename")}
        else:
            # Only update records where bytes is NULL or empty
            target_media = {}
            for m in Media.objects.only("id", "filename").iterator():
                target_media[m.filename] = m

        self.stdout.write(f"  Target DB: {len(target_media)} media records")

        # Process in batches
        stats = {"migrated": 0, "skipped_no_match": 0, "skipped_has_bytes": 0, "errors": 0}
        batch = []

        for row in src_records:
            filename = row["filename"]

            if filename not in target_media:
                stats["skipped_no_match"] += 1
                continue

            target = target_media[filename]

            # Check if target already has bytes (unless --force)
            if not force:
                has_bytes = Media.objects.filter(
                    id=target.id
                ).exclude(bytes=b"").exclude(bytes=None).exists()
                if has_bytes:
                    stats["skipped_has_bytes"] += 1
                    continue

            batch.append((row["filename"], target.id))

            if len(batch) >= batch_size:
                self._process_batch(src, batch, stats, dry_run)
                batch = []

        # Process remaining
        if batch:
            self._process_batch(src, batch, stats, dry_run)

        src.close()

        elapsed = time.time() - start
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("  MIGRATION COMPLETE"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Migrated:          {stats['migrated']}")
        self.stdout.write(f"  Skipped (no match):{stats['skipped_no_match']}")
        self.stdout.write(f"  Skipped (has data):{stats['skipped_has_bytes']}")
        self.stdout.write(f"  Errors:            {stats['errors']}")
        self.stdout.write(f"  Time:              {elapsed:.1f}s")

    def _process_batch(self, src_conn, batch, stats, dry_run):
        """Process a batch of media records."""
        for filename, target_id in batch:
            try:
                if dry_run:
                    self.stdout.write(f"  [DRY-RUN] Would migrate: {filename}")
                    stats["migrated"] += 1
                    continue

                # Read bytes from SQLite
                cursor = src_conn.execute(
                    "SELECT bytes FROM catalog_media WHERE filename = ?",
                    (filename,),
                )
                row = cursor.fetchone()
                if not row or not row["bytes"]:
                    stats["errors"] += 1
                    self.stderr.write(f"  WARNING: No bytes in SQLite for {filename}")
                    continue

                binary_data = bytes(row["bytes"])

                # Update PostgreSQL
                Media.objects.filter(id=target_id).update(bytes=binary_data)

                stats["migrated"] += 1
                if stats["migrated"] % 50 == 0:
                    self.stdout.write(f"  ... {stats['migrated']} migrated")

            except Exception as e:
                stats["errors"] += 1
                self.stderr.write(self.style.ERROR(f"  ERROR: {filename}: {e}"))
