from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson
from retainer.models import *
from decimal import *

@csrf_exempt
def put_task(request):
    if request.method == 'POST':
        params = request.POST
        if 'json' in params:
            if APIKey.needed() and not APIKey.check(params['apiKey']):
                return HttpResponse('Denied.')
            # now, add stuff from json into a ProtoHit
            json = simplejson.loads(params['json'])
            ph = ProtoHit(hit_type_id = json['hit_type_id'], 
                    title=json['title'], 
                    description=json['description'], 
                    keywords=json['keywords'], 
                    url=json['url'],
                    frame_height=json['frame_height'],
                    reward=Decimal(str(json['reward'])),
                    assignment_duration=int(json['assignment_duration']), 
                    lifetime=int(json['lifetime']),
                    max_assignments=int(json['max_assignments']),
                    auto_approval_delay=int(json['auto_approval_delay']),
                    worker_locale=json['worker_locale'],
                    approval_rating=int(json['approval_rating']))
            ph.save()
            return HttpResponse(str(ph.id))
        return HttpResponse('OK')
    elif request.method == 'GET':
        return HttpResponse('Bad request type.')