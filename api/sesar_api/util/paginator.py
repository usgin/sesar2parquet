from django.core.paginator import Paginator

def get_paginated_queryset(queryset, offset, limit):
    page_number = (offset // limit) + 1
    paginator = Paginator(queryset, limit)
    page = paginator.get_page(page_number)

    return page.object_list