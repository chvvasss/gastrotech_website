"""
Django management command to populate product category_id from series
Fixes issue where all products have NULL category_id
"""

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Populate product.category_id from series.category_id'

    def handle(self, *args, **options):
        self.stdout.write("Populating product category_id from series...")
        
        with connection.cursor() as cursor:
            # Count products without category
            cursor.execute("""
                SELECT COUNT(*) 
                FROM catalog_product 
                WHERE category_id IS NULL
            """)
            before_count = cursor.fetchone()[0]
            self.stdout.write(f"Products without category_id: {before_count}")
            
            # Update products from their series
            cursor.execute("""
                UPDATE catalog_product p
                SET category_id = s.category_id
                FROM catalog_series s
                WHERE p.series_id = s.id
                  AND p.category_id IS NULL
                  AND s.category_id IS NOT NULL
            """)
            
            updated = cursor.rowcount
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} products"))
            
            # Verify
            cursor.execute("""
                SELECT COUNT(*) 
                FROM catalog_product 
                WHERE category_id IS NULL
            """)
            after_count = cursor.fetchone()[0]
            self.stdout.write(f"Products still without category_id: {after_count}")
            
            # Show distribution by category
            cursor.execute("""
                SELECT c.name, COUNT(p.id) as product_count
                FROM catalog_product p
                JOIN catalog_category c ON p.category_id = c.id
                GROUP BY c.id, c.name
                ORDER BY product_count DESC
            """)
            
            self.stdout.write("\nProduct distribution by category:")
            for row in cursor.fetchall():
                self.stdout.write(f"  {row[0]}: {row[1]} products")
