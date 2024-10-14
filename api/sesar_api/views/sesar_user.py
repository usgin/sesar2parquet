from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from sesar_api.models import SesarUser
from sesar_api.serializers import SesarUserSerializer


# search for user by name or orcid
@api_view(['GET'])
def search_users(request):
    query = request.GET.get('query', '')
    limit = int(request.GET.get('limit', 10))
    try:
        # search for user using name or orcid
        users = SesarUser.objects.filter(
            Q(orcid__isnull=False) &
            Q(fname__icontains=query) |
            Q(lname__icontains=query) |
            Q(orcid__icontains=query) |
            Q(Q(fname__icontains=query.split()[0]) & Q(lname__icontains=query.split()[-1]))
        )[:limit]

        if users:
            serializer = SesarUserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)