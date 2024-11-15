from sesar_api.models import Sample
from django.core.exceptions import FieldError
from django.db.models import Q
from django.utils import timezone


def get_samples(filters=None, order_by=None, values=None):
    valid_fields = [f.name for f in Sample._meta.get_fields()]
    cleaned_filters = Q()

    # Default filter for archive_date (either NULL or >= current time)
    default_filter = Q(archive_date__isnull=True) | Q(archive_date__gte=timezone.now())

    if filters:
        for key, value in filters.items():
            # Check if the key is a valid field
            if key.split('__')[0] not in valid_fields:
                raise FieldError(f"Invalid field '{key}' in filters.")

            cleaned_filters &= Q(**{key: value})

    cleaned_filters &= default_filter

    try:
        queryset = Sample.objects.filter(cleaned_filters).select_related(
            'origin_sample',
            'sample_type',
            'top_level_classification',
            'classification',
            'country',
            'nav_type',
            'launch_type'
        )
        if order_by:
            queryset = queryset.order_by(order_by, 'sample_id')

        if values:
            queryset = queryset.values(*values)

        return queryset
    except FieldError as e:
        raise ValueError(f"Error in filtering: {e}")