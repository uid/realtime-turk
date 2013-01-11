from django.http import HttpResponse
from retainer.models import *

import sys

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

PING_TYPES = {
    'waiting': 'waiting',
    'working': 'working'
}

def ping(request, worker_id, assignment_id, hit_id, ping_type):
    assignment = makeOrGetAssignment(assignment_id, worker_id, hit_id)

    if assignment is None:
        return HttpResponse('Bad assignment')

    ping = PING_TYPES[ping_type]
    event = Event(assignment = assignment, event_type = ping,
                   ip = request.META['REMOTE_ADDR'],
                   user_agent = request.META['HTTP_USER_AGENT'],
                   server_time = unixtime(datetime.now()),
                   client_time = 0, # TODO: fix. add to url params or switch to POST
                   detail = '')
    event.save()
    
    return HttpResponse('OK')
                                      
def makeOrGetAssignment(assignment_id, worker_id, hit_id):
    if assignment_id == 'ASSIGNMENT_ID_NOT_AVAILABLE':
        return None
    hit = Hit.objects.get(hit_id = hit_id)
    assignment = None

    # get the assignment information
    try:
        assignment = Assignment.objects.get(assignment_id = assignment_id)
        # if necessary, update the assignment to the current hit and worker
        if assignment.worker_id != worker_id or assignment.hit_id != hit:
            assignment.hit_id = hit
            assignment.worker_id = worker_id
            assignment.save()

    except Assignment.DoesNotExist:
        assignment = Assignment(assignment_id = assignment_id, worker_id = worker_id, hit_id = hit)
        assignment.save()

    return assignment
