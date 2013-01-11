from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson

from settings import PING_TIMEOUT_SECONDS
#import cron # this is my cron module+function, nothing built-in

from retainer.models import *
from retainer.utils.request_utils import checkRequestParams
from retainer.utils.transaction import flushTransaction

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

@csrf_exempt
def make(request):
   # initialize a WorkReservation, for some time in the future
   if not checkRequestParams(request, ['apiKey', 'id', 'foreignID', 'delay', 'numAssignments']):
       return HttpResponse('Bad params')
   
   params = request.POST
   try:
       proto = ProtoHit.objects.get(id=int(params['id']))
       foreign_id = int(params['foreignID'])
       payload = params['payload'] if 'payload' in params else ''
       resv = WorkReservation(proto = proto, \
           foreign_id = foreign_id, \
           payload = payload, \
           start_time = unixtime(datetime.now() + timedelta(seconds = int(params['delay']))), \
           assignments = int(params['numAssignments']), \
           done = False, \
           invoked = False)
       resv.save()
       
       #cron.cron()
       
       return HttpResponse(resv.id)
   except ProtoHit.DoesNotExist:
       return HttpResponse('ProtoHit.DoesNotExist')

@csrf_exempt
def invoke(request):
    # supply an existing WorkReservation ID, and call it to action.
    # this will also happen automatically once the reservation's 'startTime' is reached
    if not checkRequestParams(request, ['apiKey', 'id']):
        return HttpResponse('Bad params')
    
    params = request.POST
    try:
        resv = WorkReservation.objects.get(id = int(params['id']))
        if 'foreignID' in params:
            resv.foreign_id = int(params['foreignID'])
        resv.invoked = True
        resv.save()
        
        return HttpResponse('OK')
    except WorkReservation.DoesNotExist:
        return HttpResponse('WorkReservation.DoesNotExist')

@csrf_exempt
def cancel(request):
    # prematurely cancel a reservation.  perhaps because an end user stopped the app
    if not checkRequestParams(request, ['apiKey', 'id']):
        return HttpResponse('Bad params')
    
    params = request.POST
    try:
        resv = WorkReservation.objects.get(id=int(params['id']))
        resv.done = True
        resv.save()
        return HttpResponse('OK')
    except WorkReservation.DoesNotExist:
        return HttpResponse('WorkReservation.DoesNotExist')
    return HttpResponse('OK')
    
@csrf_exempt
def finish(request):
    # mark a reservation as successfully finished
    if not checkRequestParams(request, ['apiKey', 'id']):
        return HttpResponse('Bad params')
    
    params = request.POST
    try:
        resv = WorkReservation.objects.get(id = int(params['id']))
        resv.done = True
        resv.save()
        return HttpResponse('OK')
    except WorkReservation.DoesNotExist:
        return HttpResponse('WorkReservation.DoesNotExist')

@csrf_exempt
def list(request):
    # query this server to get info about all reservations being serviced
    return HttpResponse('Unimplemented')

def unfulfilledReservations():
    return WorkReservation.objects.filter(done = False)

def unfulfilledReservationsForProto(proto):
    return WorkReservation.objects.filter(done = False, proto = proto)
    
    