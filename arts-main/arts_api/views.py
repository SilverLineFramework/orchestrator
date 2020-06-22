from django.http import JsonResponse
from django.conf import settings

def get_config(request):
    print("**HERE!", request.method)
    if request.method == 'GET':
        config = settings.PUBSUB
        #print(config)
        return JsonResponse(config)