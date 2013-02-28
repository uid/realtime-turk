#!/usr/bin/python -O

from optparse import OptionParser
from datetime import datetime, timedelta
import time

from boto.mturk.qualification import *
from django.core.management import setup_environ
import settings
if __name__ == '__main__':
    setup_environ(settings)

#FIXME: import craziness causing crashes if this script is called from a web request
from retainer.models import *
from retainer.utils.mt_connection import *
from retainer.utils.external_hit import ExternalHit
from retainer.utils.timeutils import total_seconds, unixtime
from retainer.work_approver import expire_all_hits
from retainer.reservation import unfulfilledReservationsForProto

JUST_UNDER_A_MINUTE = 54 # seconds
ACTIVE_HIT_NUM = 7

def forever():
    while True:
        postHITs()

def postHITs():
    startTime = datetime.utcnow()
    mt_conn = get_mt_conn()
    seq = 0
    hits = []
    while unixtime(datetime.utcnow()) < (unixtime(startTime) + JUST_UNDER_A_MINUTE):
        seq = (seq + 1) % ACTIVE_HIT_NUM # what's a good number of HITs?
        time.sleep(2)
        #print "seq " + str(seq) + " at " + str(unixtime(datetime.utcnow()))
        
        protos = ProtoHit.objects.all()
    
        for proto in protos:
            reservations = unfulfilledReservationsForProto(proto)
            for reservation in reservations:
                numOnRetainer = len(reservation.workers)
                #print 'num on retainer: ' + str(numOnRetainer) + ' for ' + str(reservation)
            
                if unixtime(datetime.now()) > (reservation.start_time + settings.RESERVATION_TIMEOUT_MINUTES * 60):
                    print 'not yet expiring: ' + str(reservation)
                    #break
                
                # how many HITs are we already maintaining for this reservation?
                existing_hits = Hit.objects.filter(reservation = reservation, removed = False)
                num_existing_hits = len(existing_hits)
                
                print 'existing hits: ' + str(existing_hits)
                
                if num_existing_hits < ACTIVE_HIT_NUM:
                    hit = postHIT(mt_conn, reservation, seq)
                    hits.append(hit)
                else: # need to delete the oldest hits for this reservation
                    oldest = existing_hits.extra(order_by = ['-creation_time'])[0]
                    print 'removing old HIT: ' + str(oldest)
                    try:
                        mt_conn.expire_hit(oldest.hit_id)
                        oldest.removed = True
                        oldest.save()
                    except Exception, e:
                        print 'could not remove the HIT for some reason'
                
            
                # postHITs for this reservation, if needed
                #if numOnRetainer < reservation.assignments:
                #    hit = postHIT(mt_conn, reservation, seq)
                #    hits.append(hit)
    
    return hits

def postHIT(mt_conn, resv, seq):
    proto = resv.proto
    
    qual_arr = []
    if proto.worker_locale != '' and proto.worker_locale is not None:
        qual_arr.append(LocaleRequirement('EqualTo', proto.worker_locale))
    if proto.approval_rating > 0:
        qual_arr.append(PercentAssignmentsApprovedRequirement('GreaterThan', proto.approval_rating))
    
    quals = Qualifications(qual_arr)
    
    seq_str = " [" + str(seq) + "]"
    
    eh = ExternalHit(title=proto.title + seq_str,
                     description = proto.description + seq_str,
                     keywords = proto.keywords,
                     url = proto.url,
                     frame_height = proto.frame_height,
                     reward_as_usd_float = float(proto.reward),
                     assignment_duration = proto.assignment_duration,
                     lifetime = proto.lifetime,
                     max_assignments = proto.max_assignments,
                     qualifications = quals,
                     auto_approval_delay = proto.auto_approval_delay)
    try:
        turk_hit = eh.post(mt_conn)
        print "Posted HIT ID " + turk_hit.HITId + " for reservation: " + str(resv)
            
        django_hit = Hit(proto_id = proto.id,
                          hit_id = turk_hit.HITId,
                          reservation = resv,
                          hit_type_id = proto.hit_type_id, 
                          title = proto.title  + seq_str, 
                          description = proto.description  + seq_str, 
                          keywords = proto.keywords, 
                          url = proto.url, 
                          reward = proto.reward,
                          assignment_duration = proto.assignment_duration, 
                          lifetime = proto.lifetime,
                          max_assignments = proto.max_assignments,
                          auto_approval_delay = proto.auto_approval_delay,
                          worker_locale = proto.worker_locale,
                          approval_rating = proto.approval_rating,
                          creation_time = unixtime(datetime.utcnow()))
        django_hit.save()
        return django_hit
            
    except Exception, e:
        print "Got exception posting HIT:\n" + str(e)

if __name__ == '__main__':
    forever()