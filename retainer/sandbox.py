from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from retainer.models import *
from retainer.utils.request_utils import checkRequestParams

@csrf_exempt
def status(request):
    if not checkRequestParams(request, ['apiKey', 'hitType']):
        return HttpResponse('Bad params')
    
    params = request.POST
    try:
        proto = ProtoHit.objects.get(hit_type_id=params['hitType'])
        return HttpResponse(str(proto.sandbox).lower())
    except ProtoHit.DoesNotExist:
        return HttpResponse('ProtoHit.DoesNotExist')
    
    return HttpResponse('OK')

@csrf_exempt
def toggle(request):
    if not checkRequestParams(request, ['apiKey', 'hitType', 'sandbox']):
        return HttpResponse('Bad params')
    
    params = request.POST
    try:
        proto = ProtoHit.objects.get(hit_type_id=params['hitType'])
        proto.sandbox = params['sandbox'] == 'true'
        print(params['sandbox'])
        print(proto.sandbox)
        proto.save()
        
        return HttpResponse('OK')
    except ProtoHit.DoesNotExist:
        return HttpResponse('ProtoHit.DoesNotExist')
    
    return HttpResponse('OK')