
from django.core.management.base import BaseCommand
from apps.catalog.models import ProductMedia
from django.utils import timezone
from datetime import timedelta
from apps.ops.management.commands.import_images import SMART_MAPPINGS

class Command(BaseCommand):
    help = 'Detects and optionally deletes mismatched product images based on filename and model code'

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Actually delete the mismatched links',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='How many days back to check (default: 1)',
        )

    def handle(self, *args, **options):
        commit = options['commit']
        days = options['days']
        
        # Filter by media creation time
        cutoff = timezone.now() - timedelta(days=days)
        
        # Get links where media was created recently
        links = ProductMedia.objects.select_related('product', 'media').filter(
            media__created_at__gte=cutoff
        )

        self.stdout.write(f"Checking {links.count()} links created within last {days} days...")
        
        mismatches = []
        
        for pm in links:
            product = pm.product
            media = pm.media
            filename = media.filename.lower()
            base_filename = filename.split('.')[0]
            
            # Get variant codes
            variants = product.variants.all()
            if not variants:
                continue

            model_codes = [v.model_code.lower() for v in variants if v.model_code]
            
            # Check matches
            is_match = False
            
            # 1. Check SMART_MAPPINGS
            mapped_code = SMART_MAPPINGS.get(base_filename)
            if mapped_code:
                if mapped_code.lower() in model_codes:
                    is_match = True
            
            # 2. Check strict containment if no smart match
            if not is_match:
                for code in model_codes:
                    # Clean code and filename 
                    code_clean = "".join(c for c in code if c.isalnum())
                    filename_clean = "".join(c for c in base_filename if c.isalnum())
                    
                    if code_clean in filename_clean:
                        is_match = True
                        break
            
            if not is_match:
                mismatches.append(pm)
                variants_str = ", ".join(model_codes[:3])
                self.stdout.write(f"MISMATCH: {product.name[:30]} ({variants_str}) - File '{media.filename}'")

        self.stdout.write(f"\nFound {len(mismatches)} mismatches.")

        if commit:
            # Delete without input for automation (assuming user approval logic handled by agent)
            # or use --no-input flag if standard, but here we just do it if --commit is passed.
            count = 0
            for pm in mismatches:
                pm.delete()
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} mismatched links."))
        else:
            self.stdout.write(self.style.WARNING("Dry run finished. Use --commit to delete."))
