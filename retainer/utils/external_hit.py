from xml.sax.saxutils import escape

import logging
import settings

from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price

class ExternalHit():
    def __init__(self, title, description, keywords, url, frame_height, 
                 reward_as_usd_float, assignment_duration, lifetime, max_assignments, 
                 auto_approval_delay, qualifications):
        self.title = title
        self.description = description
        self.keywords = keywords
        self.url = url
        self.frame_height = frame_height
        self.reward_as_usd_float = reward_as_usd_float
        self.assignment_duration = assignment_duration
        self.lifetime = lifetime
        self.max_assignments = max_assignments
        self.auto_approval_delay = auto_approval_delay
        self._question = ExternalQuestion(escape(self.url), self.frame_height)
        self._price = Price(self.reward_as_usd_float)
        self.qualifications = qualifications


    def post(self, conn):
        hits = conn.create_hit(hit_type=None,
                               question=self._question,
                               lifetime=self.lifetime,
                               max_assignments=self.max_assignments,
                               title=self.title,
                               description=self.description,
                               keywords=self.keywords,
                               reward=self._price,
                               duration=self.assignment_duration,
                               approval_delay=self.auto_approval_delay,
                               annotation=None,
                               #qual_req=None,
                               questions=None,
                               qualifications=self.qualifications,
                               response_groups=None)
        register_all_notifications_for_hit_type(conn, hits[0].HITTypeId)
        return hits[0]




def register_all_notifications_for_hit_type(conn, hit_type):
    # TODO: maybe some error handling? maybe put in a different file?
    conn.set_rest_notification(str(hit_type),
                               "http://" + settings.HIT_SERVER + "/mt_notification",
                               event_types=("AssignmentAccepted", "AssignmentAbandoned", "AssignmentReturned", "AssignmentSubmitted", "HITReviewable", "HITExpired"))
