from sesar_api.models import Sample
from django.core.exceptions import FieldError


def get_samples(filters, order_by, offset, limit):

    valid_fields = [f.name for f in Sample._meta.get_fields()]
    cleaned_filters = {}

    for key, value in filters.items():
        # Check if the key is a valid field
        if key.split('__')[0] not in valid_fields:
            raise FieldError(f"Invalid field '{key}' in filters.")

        # TODO: Add type-checking

        cleaned_filters[key] = value

    try:
        # Use the cleaned filters to perform the query
        queryset = Sample.objects.filter(**cleaned_filters)
        if order_by:
            queryset = queryset.order_by(order_by)
        
        if offset and limit:
            queryset = queryset[offset:offset+limit]

        return queryset
    except FieldError as e:
        raise ValueError(f"Error in filtering: {e}")