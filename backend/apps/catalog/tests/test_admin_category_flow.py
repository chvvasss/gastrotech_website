import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.catalog.models import Category, Series, Product, Brand

@pytest.mark.django_db
class TestAdminCategoryFlow:
    def setup_method(self):
        self.client = APIClient()
        # Create user effectively (mocking permissions if needed, but easier to use force_authenticate if we had a user factory)
        # For now, we assume IsAdminOrEditor is checked. We might need to mock or create a superuser.
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_superuser(username='admin', password='password')
        self.client.force_authenticate(user=self.user)

        # Setup Data
        self.category = Category.objects.create(name="Test Cat", slug="test-cat", order=1)
        self.series = Series.objects.create(name="Test Series", slug="test-series", category=self.category, order=1)
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")
        self.product = Product.objects.create(
            title_tr="Test Product", 
            slug="test-product", 
            series=self.series, 
            brand=self.brand,
            status="active"
        )
        # Needs variant to count? ViewSet counts 'series__products'.
        # Product creation usually enough.

    def test_category_list_includes_counts(self):
        url = reverse('admin-categories-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()['results']
        assert len(data) >= 1
        cat_data = next(d for d in data if d['slug'] == 'test-cat')
        
        # Check counts
        assert cat_data['series_count'] == 1
        assert cat_data['products_count'] == 1

    def test_category_detail_includes_series_and_counts(self):
        url = reverse('admin-categories-detail', args=['test-cat'])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check standard fields
        assert data['slug'] == 'test-cat'
        assert data['products_count'] == 1
        
        # Check nested series
        assert 'series' in data
        assert len(data['series']) == 1
        assert data['series'][0]['slug'] == 'test-series'
        
        # Check series fields
        # Note: Series serializer might have products_count if we updated it
        # Let's check if it does (we added it)
        # Wait, AdminSeriesSerializer has products_count but it relies on annotation in the ViewSet.
        # Nested serializer usage:
        # standard ModelSerializer won't have the annotation from the PARENT queryset.
        # The parent queryset annotation 'products_count' belongs to the category.
        # The series list is serialized via 'series = AdminSeriesSerializer(many=True)'.
        # Since it's a nested relationship, we are NOT using AdminSeriesViewSet.get_queryset().
        # So the Series objects in `category.series.all()` will NOT have `products_count` annotated unless we do something special in `AdminCategoryDetailSerializer` or the ViewSet query.
        # Let's see if the test fails. It likely WILL fail for series.products_count.
        
        # We can fix this by using a SerializerMethodField for counts in nested objects if annotation is missing.
