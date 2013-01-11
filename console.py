from optparse import OptionParser
from datetime import datetime, timedelta
import time
import random
import os

from boto.mturk.qualification import *

from django.core.management import setup_environ
import settings
setup_environ(settings)

from retainer.models import *
from retainer.utils.mt_connection import *
from retainer.utils.external_hit import ExternalHit
from retainer.utils.timeutils import total_seconds, unixtime
from retainer.work_approver import expire_all_hits
from retainer.gettask import waiting_workers

TIME_BETWEEN_RUNS = 5 # seconds
TIME_BETWEEN_HIT_POSTINGS = 30 # seconds

MIN_ON_RETAINER = settings.MIN_WAITING_WORKERS # WARNING, this value should be > 1 unless testing alone
MAX_WORKERS = 60

def quikTurKit(num_hits, hit_type):
    """ Keeps posting HITs """
    mt_conn = get_mt_conn()
    hits_posted = 0
    
    try:
        last_hit_post = datetime.now()
        num_on_retainer = -1
        
# HQ: seems study specific. Removed and just calls postHITs now
#        postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version)
        hits_posted += num_hits
        postHITs(num_hits, hit_type, mt_conn)

        keep_going = True
        while keep_going:
            start_run = datetime.now()
            
            if start_run - last_hit_post >= timedelta(seconds = TIME_BETWEEN_HIT_POSTINGS):

# HQ: seems study specific. Removed and just calls postHITs now
#               postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version)
                if hits_posted < MAX_WORKERS:
                    postHITs(num_hits, hit_type, mt_conn)
                    hits_posted += num_hits
                
                    last_hit_post = start_run
                print("Warning: not approving HITs. Do in another script.")            

                # approve_kyle_hits_and_clean_up(verbose=False, dry_run=False)
                #keep_going = postNewVideos(db, version)
                if len(getIncompleteProtos(hit_type)) > 0:
                    print("HITs posted: " + str(hits_posted) + "/" + str(MAX_WORKERS))
                    keep_going = True
                else:
                    keep_going = False
            
            sleep_count = 0
            while sleep_count < TIME_BETWEEN_HIT_POSTINGS:
                start_run = datetime.now()
                time.sleep(1)
                sleep_count += 1
                now_on_retainer = len(waiting_workers())
                if num_on_retainer != now_on_retainer:
                    print "Workers on retainer: " + str(now_on_retainer)
                    num_on_retainer = now_on_retainer
                
    except KeyboardInterrupt:
        print("Caught Ctrl-C. Exiting...")
    finally:
        expire_all_hits(mt_conn)
        ##approve_kyle_hits_and_clean_up(verbose=False, dry_run=False)

def postHITs(num_hits, hit_type, mt_conn):
    """ Posts HITs to MTurk with the given parameters"""
    
    protos = getIncompleteProtos(hit_type)
    
    if len(protos) <= 0:
        print("Warning: Retainer starting without any types of HIT to post")
        return
    proto = protos[0]
    
    qual_arr = []
    if proto.worker_locale != '' and proto.worker_locale is not None:
        qual_arr.append(LocaleRequirement('EqualTo', proto.worker_locale))
    if proto.approval_rating > 0:
        qual_arr.append(PercentAssignmentsApprovedRequirement('GreaterThan', proto.approval_rating))
    
    quals = Qualifications(qual_arr)
    
    eh = ExternalHit(title=proto.title,
                     description=proto.description,
                     keywords=proto.keywords,
                     url=proto.url,
                     frame_height=1200,
                     reward_as_usd_float=float(proto.reward),
                     assignment_duration=proto.assignment_duration,
                     lifetime=proto.lifetime,
                     max_assignments=proto.max_assignments,
                     qualifications=quals,
                     auto_approval_delay=proto.auto_approval_delay) # 1 day
    
    

    for i in range(num_hits):
        try:
            turk_hit = eh.post(mt_conn)
            print "Posted HIT ID " + turk_hit.HITId
            
            django_hit = Hit(proto_id = proto.id,
                              hit_id=turk_hit.HITId,
                              hit_type_id = proto.hit_type_id, 
                              title=proto.title, 
                              description=proto.description, 
                              keywords=proto.keywords, 
                              url=proto.url, 
                              reward=proto.reward, 
                              assignment_duration=proto.assignment_duration, 
                              lifetime=proto.lifetime,
                              max_assignments=proto.max_assignments,
                              auto_approval_delay=proto.auto_approval_delay,
                              worker_locale=proto.worker_locale,
                              approval_rating=proto.approval_rating,
                              retainertime=proto.retainertime)
            django_hit.save()
            
        except Exception, e:
            print "Got exception posting HIT:\n" + str(e)

def getIncompleteProtos(hit_type):
    if hit_type == "":
        protos = ProtoHit.objects.filter(done = False)
    else:
        protos = ProtoHit.objects.filter(hit_type_id = hit_type, done = False)
    return protos

if __name__ == "__main__":
    if settings.SANDBOX:
        wait_bucket = 4 * 60
    else:
        wait_bucket = 4 * 60
    
    if MIN_ON_RETAINER < 4 and not settings.SANDBOX:
        raise Exception("Not enough people on retainer for non-sandbox tasks! Are you sure?")

    # Parse the options
    parser = OptionParser()
    parser.add_option("-n", "--number-of-hits", dest="number_of_hits", help="NUMBER of hits", metavar="NUMBER", default = 3)
    parser.add_option("-t", "--type", dest="type", help="TYPE of hit to post", metavar="TYPE", default = "")
    
    (options, args) = parser.parse_args()
    
    t = options.type
    n = int(options.number_of_hits)
    
    print "Posting " + str(n) + " HITs at a time based on -n argument."
    
    quikTurKit(n, t)
