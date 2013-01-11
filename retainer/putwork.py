from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson
from retainer.models import *

@csrf_exempt
def put_work(request):
    if request.method == 'POST':
        params = request.POST
        if 'api_key' in params and 'id' in params:
            if not APIKey.check(params['apiKey']) and APIKey.needed():
                return HttpResponse('Denied.')
            # all clear
            try:
                proto = ProtoHit.objects.get(id=int(params['id']))
                foreign_id = int(params['foreign_id']) if 'foreign_id' in params else 0
                payload = params['payload'] if 'payload' in params else ''
                work_req = WorkRequest(proto=proto, foreign_id = foreign_id, payload = payload)
                work_req.save()
                return HttpResponse(work_req.id)
            except ProtoHit.DoesNotExist:
                return HttpResponse('ProtoHit.DoesNotExist')
        else:
            return HttpResponse('id must be specified')
    elif request.method == 'GET':
        return HttpResponse('Bad request type.')

@csrf_exempt
def finish_work(request):
    """
    Responds to requests like /putwork/done, with POST params api_key, id (WorkRequest.id), 
        optional param false (sets 'done' to False), which is the opposite of the default behavior
    """
    if request.method == 'POST':
        params = request.POST
        if 'api_key' in params and 'id' in params:
            if not APIKey.check(params['api_key']):
                return HttpResponse('Denied.')
            try: 
                work_req = WorkRequest.objects.get(id=int(params['id']))
                if 'false' in params:
                    work_req.done = False
                else:
                    work_req.done = True
                work_req.save()
                return HttpResponse('OK')
            except WorkRequest.DoesNotExist:
                return HttpResponse('WorkRequest.DoesNotExist')
        else:
            return HttpResponse('id must be specified')
    elif request.method == 'GET':
        return HttpResponse('Bad request type.')
