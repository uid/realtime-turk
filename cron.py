#!/usr/bin/python -O

from optparse import OptionParser
from datetime import datetime, timedelta
import time
import random
import os


from boto.mturk.qualification import *
from django.core.management import setup_environ
import settings
if __name__ == '__main__':
    setup_environ(settings)

#FIXME: 
from retainer.models import *
from retainer.utils.mt_connection import *
from retainer.utils.external_hit import ExternalHit
from retainer.utils.timeutils import total_seconds, unixtime
from retainer.work_approver import expire_all_hits
from retainer.reservation import unfulfilledReservationsForProto


# this is the 'cron' script entry point
def cron():
    mt_conn = get_mt_conn()
    print datetime.utcnow().strftime("%m.%d.%Y %I:%M:%S %p") + ' --- retainer cron job ---'
    protos = ProtoHit.objects.all()
    
    for proto in protos:
        reservations = unfulfilledReservationsForProto(proto)
        for reservation in reservations:
            numOnRetainer = len(reservation.workers)
            print 'num on retainer: ' + str(numOnRetainer) + ' for ' + str(reservation)
            
            if unixtime(datetime.now()) > (reservation.start_time + settings.RESERVATION_TIMEOUT_MINUTES * 60):
                print 'expired, not posting more HITs for this reservation'
                break
            
            # postHITs for this reservation, if needed
            if numOnRetainer < reservation.assignments:
                postHITs(mt_conn, reservation)

def expire(mt_conn):
    expire_all_hits(mt_conn)

def postHITs(mt_conn, resv):
    """ Posts HITs to MTurk with the given parameters"""
    
    proto = resv.proto
    
    qual_arr = []
    if proto.worker_locale != '' and proto.worker_locale is not None:
        qual_arr.append(LocaleRequirement('EqualTo', proto.worker_locale))
    if proto.approval_rating > 0:
        qual_arr.append(PercentAssignmentsApprovedRequirement('GreaterThan', proto.approval_rating))
    
    quals = Qualifications(qual_arr)
    
    eh = ExternalHit(title=proto.title,
                     description = proto.description,
                     keywords = proto.keywords,
                     url = proto.url,
                     frame_height = proto.frame_height,
                     reward_as_usd_float = float(proto.reward),
                     assignment_duration = proto.assignment_duration,
                     lifetime = proto.lifetime,
                     max_assignments = proto.max_assignments,
                     qualifications = quals,
                     auto_approval_delay = proto.auto_approval_delay)

    for i in range(settings.HITS_PER_CRON):
        try:
            turk_hit = eh.post(mt_conn)
            print "Posted HIT ID " + turk_hit.HITId
            
            django_hit = Hit(proto_id = proto.id,
                              hit_id = turk_hit.HITId,
                              reservation = resv,
                              hit_type_id = proto.hit_type_id, 
                              title = proto.title, 
                              description = proto.description, 
                              keywords = proto.keywords, 
                              url = proto.url, 
                              reward = proto.reward,
                              assignment_duration = proto.assignment_duration, 
                              lifetime = proto.lifetime,
                              max_assignments = proto.max_assignments,
                              auto_approval_delay = proto.auto_approval_delay,
                              worker_locale = proto.worker_locale,
                              approval_rating = proto.approval_rating)
            django_hit.save()
            
        except Exception, e:
            print "Got exception posting HIT:\n" + str(e)
        
if __name__ == '__main__':
    cron()