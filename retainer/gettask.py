from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max

import json
import simplejson
import settings

from retainer.models import *
from retainer.ping import PING_TYPES
from retainer.utils.transaction import flushTransaction
from retainer.reservation import unfulfilledReservationsForProto

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

# Get a task for the worker, or assign one if we can
@csrf_exempt # michael suggests: @commit_on_success
def getTask(request, assignment_id):
    # find out whether the worker has already been assigned a task. if so, just return that task.
    current_assignments = Assignment.objects.filter(assignment_id = assignment_id)
    
    current = current_assignments[0] if len(current_assignments) > 0 else None
    if current is None:
        return HttpResponse('Bad assignment')
    if current.task_id is not None:
        taskInfo = { 'start': True, 'taskID': int(current.task_id) }
    else:
        proto = current.hit_id.proto
        resv = current.hit_id.reservation
        
        siblings = resv.siblings.filter(done=False, invoked=True)
        
        if resv.invoked and not resv.done and len(resv.workers) <= resv.assignments:
            tid = resv.foreign_id
            current.task_id = tid
            taskInfo = { 'start': True, 'taskID': int(tid) }
            current.save()
        elif len(siblings) > 0:
            assigned = False
            for sibling in siblings:
                if len(sibling.workers) <= sibling.assignments:
                    tid = sibling.foreign_id
                    current.task_id = tid
                    taskInfo = { 'start': True, 'taskID': int(tid) }
                    current.save()
                    assigned = True
            if not assigned:
                taskInfo = { 'start': False }
        else:
            taskInfo = { 'start': False }

    # now turn the taskInfo python into JSON to return to the client
    return HttpResponse(simplejson.dumps(taskInfo), mimetype="application/json")

def save_assignment_task_map(assignment_map):
    for assignment_id in assignment_map.keys():
        task_id = assignment_map[assignment_id]
        assignment = Assignment.objects.get(assignment_id = assignment_id)
        assignment.task_id = task_id
        assignment.save()


