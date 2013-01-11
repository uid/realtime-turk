import settings

import mt_connection
from decimal import Decimal

from datetime import datetime
import retainer.utils.timeutils

def print_assignment_details(a, indent=""):
    print indent + "Status: " + a.AssignmentStatus
    print indent + "SubmitTime: " + a.SubmitTime
    print indent + "AutoApprovalTime: " + a.AutoApprovalTime
    print indent + "Answer: " + str(reformat_external_question_answer(a.answers, a.AssignmentId))

def reformat_external_question_answer(answer_array, assignmentid):
    """
    reformats an answer array from an External Question into a dict
    Note: if there are repeated element names in the answer array, the last value will be used
    """

    a = {}
    for ans in answer_array:
        for q in ans:
            for field in q.fields:
                a[field[0]] = field[1]
    a['assignmentId'] = assignmentid
    return a


def review_assignment(conn,
                      assignment,
                      answer_reviewer=lambda x: (True, None), 
                      bonus_evaluator=lambda x: (False, None, None),
                      verbose=True,
                      indent="",
                      dry_run=False):
    """
    reviews passed in assignment using the functions passed in

    returns one of 'approved', 'approvedbonused', 'rejected', or 'skipped'
    
    conn:
      a mechanical turk connection

    assignment:
      the assignment to review

    answer_reviewer:
      a function that takes an answer dict and returns either the tuple
        (approved[True|False], "approval message" or None)
      or 'None' if it does not know how to review

    bonus_evaluator:
      a function that takes an answer dict and returns a tuple
        (bonused[True|False], bonus amount or None, "bonus message" or None)
      This function will only be called if answer_reviewer approved the answer
      To grant a bonus, both bonus amount and bonus message must be given

    verbose:
      print out details about the assignment when processing

    indent: 
      a string to indent each line of output by
    """
    result = None

    print indent + "Assignment ID: " + assignment.AssignmentId
    if verbose:
        print_assignment_details(assignment, indent=indent)
    parsed_answers = reformat_external_question_answer(assignment.answers, assignment.AssignmentId)

    review = answer_reviewer(parsed_answers)
    if review == None: # chose not to review this assignment
        print indent + "ASSIGNMENT SKIPPED"
        result = 'skipped'
    else:
        (approved, msg) = review

        if approved:
            if msg == None:
                msg = "Assignment approved, thanks."
            (bonused, amount, bonusmsg) = bonus_evaluator(parsed_answers)

            if bonused and amount != None:
                if bonusmsg == None:
                    bonusmsg = "Bonus of " + str(amount) + " granted."
                msg = msg + " " + bonusmsg
                
            if not dry_run:
                conn.approve_assignment(assignment.AssignmentId, msg)

            print indent + "ASSIGNMENT APPROVED " + msg

            result = 'approved'

            if dry_run:
                print indent + "(dry run -- assignment not actually approved)"
                

            if bonused and amount != None and bonusmsg != None:
                if not dry_run:
                    conn.grant_bonus(assignment.WorkerId, 
                                     assignment.AssignmentId, 
                                     conn.get_price_as_price(amount),
                                     bonusmsg)
                print indent + "ASSIGNMENT BONUSED: " + str(amount) + " " + str(bonusmsg)

                result = 'approvedbonused'

                if dry_run:
                    print indent + "(dry run -- no bonus actually granted)"
            else:
                print indent + "NO BONUS"

        else: # not approved
            if not dry_run:
                conn.reject_assignment(assignment.AssignmentId, msg)

            if msg:
                print indent + "ASSIGNMENT REJECTED " + msg
            else:
                print indent + "ASSIGNMENT REJECTED"
            
            result = 'rejected'

            if dry_run:
                print indent + "(dry run -- assignment not actually rejected)"


    return result

    
def review_pending_assignments(conn,
                               answer_reviewer=lambda x: (True, None), 
                               bonus_evaluator=lambda x: (False, None, None),
                               verbose=True,
                               dry_run=False):
    """
    reviews all pending assignments, calling "review assignment" for each
    
    returns number of assignments successfully reviewed

    See documentation for "review_assignment" for description of parameters
    """

    counts = {'approved':0, 'approvedbonused':0, 'rejected':0, 'skipped':0, 'errors':0}

    hits = get_all_reviewable_hits(conn)
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = conn.get_assignments(h.HITId, status="Submitted")
        for a in assignments:
            result = review_assignment(conn, a, 
                                       answer_reviewer=answer_reviewer, 
                                       bonus_evaluator=bonus_evaluator,
                                       verbose=verbose,
                                       indent="  ",
                                       dry_run=dry_run)
            if result != None:
                counts[result] += 1
            else:
                counts['errors'] += 1
    return counts
        

def get_all_reviewable_hits(conn):
    hits = []
    page_size = 100

    page = 1
    additional_hits = conn.get_reviewable_hits(page_number=page, page_size=page_size, sort_by="Enumeration", status="Reviewable")
    while len(additional_hits) > 0:
        hits.extend(additional_hits)
        page += 1
        additional_hits = conn.get_reviewable_hits(page_number=page, page_size=page_size, sort_by="Enumeration", status="Reviewable")

    page = 1
    additional_hits = conn.get_reviewable_hits(page_number=page, page_size=page_size, sort_by="Enumeration", status="Reviewing")
    while len(additional_hits) > 0:
        hits.extend(additional_hits)
        page += 1
        additional_hits = conn.get_reviewable_hits(page_number=page, page_size=page_size, sort_by="Enumeration", status="Reviewing")

    return hits

def get_all_hits(conn):
    hits = []
    page_size = 100

    page = 1
    additional_hits = conn.search_hits(page_number=page, page_size=page_size, sort_by="Enumeration")
    while len(additional_hits) > 0:
        hits.extend(additional_hits)
        page += 1
        additional_hits = conn.search_hits(page_number=page, page_size=page_size, sort_by="Enumeration")

    return hits
    


def clean_up_old_hits(conn, verbose=True, dry_run=False):
    counts = {'cleaned':0, 'remaining':0, 'errors':0}
    hits = get_all_hits(conn)
    now = timeutils.unixtime(datetime.now())
    for h in hits:
        try:
            num_to_be_reviewed = len(conn.get_assignments(h.HITId, status="Submitted")) # yet to be reviewed        
            if verbose:
                print "------------------"
                print "HIT ID: " + h.HITId
                expiration = timeutils.parseISO(h.Expiration)
                duration = Decimal(h.AssignmentDurationInSeconds)
                print "Expiration: " + str(expiration)
                print "isExpired: " + str(h.expired)
                print "AssignmentDuration: " + str(duration)
                print "Seconds until last assignment can be turned in: " + str((float(expiration)+float(duration))-float(now))
                print "HITStatus: " + h.HITStatus
                print "Yet-to-be-reviewed assignments: " + str(num_to_be_reviewed)
                print "Approved assignments: " + str(len(conn.get_assignments(h.HITId, status="Approved")))
                print "Rejected assignments: " + str(len(conn.get_assignments(h.HITId, status="Rejected")))
            if (h.HITStatus == 'Reviewable' or h.HITStatus == 'Reviewing') and num_to_be_reviewed == 0:
                if not dry_run:
                    conn.dispose_hit(h.HITId)
                print "DISPOSED OF HIT"
                counts['cleaned'] += 1
                if dry_run:
                    print "(dry run -- HIT not actually disposed)"
            else:
                counts['remaining'] += 1
        except Exception, e:
            print "exception processing HIT:\n" + str(e)
            counts['errors'] += 1
            
    return counts




def print_all_pending_answers(conn):
    hits = get_all_reviewable_hits(conn)
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = conn.get_assignments(h.HITId, status="Submitted")
        for a in assignments:
            print "  Assignment ID: " + a.AssignmentId
            print_assignment_details(a, indent="  ")

def autoapprove_all_reviewable_assignments(conn, verbose=True, dry_run=False):
    return review_pending_assignments(conn, 
                                      answer_reviewer=lambda x: (True, None),
                                      bonus_evaluator=lambda x: (False, None, None),
                                      verbose=verbose,
                                      dry_run=dry_run)

def expire_all_hits(conn):
    """This will expire all the HITs in your account so that
    nobody else can grab them. Good thing to do to clean up quikTurKit"""
    count = 0
    try:
        assignable_hits = [hit for hit in get_all_hits(conn) if hit.HITStatus == "Assignable"]
        
        for h in assignable_hits:
            try:
                print "Expiring HIT " + h.HITId
                conn.expire_hit(h.HITId)
                count += 1
            except Exception, e:
                print "ERROR EXPIRING HIT " + h.HITId + "\n" + str(e)

    except Exception, e:
            print "Big error: \n" + str(e)

    print "ALL DONE! Expired " + str(count) + " HITs"

    return count
    
                    
def delete_all_hits(conn, do_you_mean_it="NO"):
    if do_you_mean_it != "YES_I_MEAN_IT":
        print """
This will delete everything in your mechanical turk account
and autoapprove everything that hasn't been approved
if you realy mean it, run:

    dispose_all_hits(conn, do_you_mean_it='YES_I_MEAN_IT')
"""
        return 0

    else:
        count = 0
        try:
            hits = conn.search_hits(page_size=100)
            while len(hits) > 0:
                for h in hits:
                    try:
                        if h.HITStatus == "Reviewable":
                            # have to approve all, then call dispose_hit
                            print "Reviewing HIT " + h.HITId

                            assignments = conn.get_assignments(h.HITId, status="Submitted")
                            while len(assignments) > 0:
                                for a in assignments:
                                    print "Approving Assignment " + a.AssignmentId
                                    conn.approve_assignment(a.AssignmentId)
                                assignments = conn.get_assignments(h.HITId, status="Submitted")                                

                            print "Assignments approved, Disposing HIT " + h.HITId
                            conn.dispose_hit(h.HITId)

                        else: # can call disable hit
                            print "Disabling HIT " + h.HITId
                            conn.disable_hit(h.HITId)

                        count += 1
                        print "SUCCESS! THE HIT IS GONE!"
                    except Exception, e:
                        print "ERROR DELETING HIT " + h.HITId + "\n" + str(e)

                hits = conn.search_hits(page_size=100)

        except Exception, e:
                print "Big error: \n" + str(e)

        print "ALL DONE! Deleted " + str(count) + " HITs"

        return count
