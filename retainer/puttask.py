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
            ph = ProtoHit.objects.get_or_create(hit_type_id = json['hit_type_id'])[0] 
            ph.title = json['title']
            ph.description = json['description']
            ph.keywords = json['keywords']
            ph.url = json['url']
            ph.frame_height = json['frame_height']
            ph.reward = Decimal(str(json['reward']))
            ph.assignment_duration = int(json['assignment_duration'])
            ph.lifetime = int(json['lifetime'])
            ph.max_assignments = int(json['max_assignments'])
            ph.auto_approval_delay = int(json['auto_approval_delay'])
            ph.worker_locale = json['worker_locale']
            ph.approval_rating = int(json['approval_rating'])
            ph.save()
            return HttpResponse(str(ph.id))
        return HttpResponse('OK')
    elif request.method == 'GET':
        return HttpResponse('Bad request type.')