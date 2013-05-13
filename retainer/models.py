from django.db import models
from datetime import datetime, timedelta
from decimal import *

from settings import PING_TIMEOUT_SECONDS

import simplejson as json

from retainer.utils.timeutils import unixtime
from retainer.utils.transaction import flushTransaction


class Assignment(models.Model):
    assignment_id =         models.CharField(primary_key=True, max_length=255)
    worker_id =             models.CharField(max_length=255, db_index=True)
    hit_id =                models.ForeignKey('Hit')
    task_id =               models.IntegerField(null=True, blank=True)
    accept_time =           models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    return_time =           models.DecimalField(decimal_places=3, null=True, max_digits=19, blank=True)
    show_time =             models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    go_time =               models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    submit_time =           models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)

    def __unicode__(self):
        return self.assignment_id

class Hit(models.Model):
    hit_id =                models.CharField(max_length=255, primary_key=True)
    reservation =           models.ForeignKey('WorkReservation')
    hit_type_id =           models.CharField(max_length=255, blank=True)
    proto =                 models.ForeignKey('ProtoHit')
    creation_time =         models.DecimalField(null=True, max_digits=19, decimal_places=3, blank=True)
    title =                 models.TextField(blank=True)
    description =           models.TextField(blank=True)
    keywords =              models.TextField(blank=True)
    url =                   models.CharField(max_length=1023)
    reward =                models.DecimalField(max_digits=6, decimal_places=2)
    frame_height =          models.IntegerField(default = 1200)
    assignment_duration =   models.IntegerField(default = 300)
    lifetime =              models.IntegerField(default = 1000)
    max_assignments =       models.IntegerField(default = 5)
    auto_approval_delay =   models.IntegerField(null=True, blank=True)
    approval_rating =       models.IntegerField(default=0)
    worker_locale =         models.CharField(max_length=255, blank=True)
    paid =                  models.BooleanField(default=False)
    removed =               models.BooleanField(default=False)

    def __unicode__(self):
        return self.hit_id

class ProtoHit(models.Model):
    hit_type_id =           models.CharField(max_length=255, null=False, unique=True)
    title =                 models.TextField(blank=True)
    description =           models.TextField(blank=True)
    keywords =              models.TextField(blank=True)
    url =                   models.CharField(max_length=1023, default='http://google.com')
    frame_height =          models.IntegerField(default = 1200)
    reward =                models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.05'))
    assignment_duration =   models.IntegerField(default=600)
    lifetime =              models.IntegerField(default=3600)
    max_assignments =       models.IntegerField(default=1)
    auto_approval_delay =   models.IntegerField(null=True, blank=True, default=86400)
    approval_rating =       models.IntegerField(default=0)
    worker_locale =         models.CharField(max_length=255, blank=True, default='')
    sandbox =               models.BooleanField(default=True)
    
    @property
    def objectify(self):
        return { \
            'id': self.id, \
            'hitTypeID': self.hit_type_id, \
            'title': self.title, \
            'url': self.url
        }
    
    def __unicode__(self):
        return self.hit_type_id + u'::' + unicode(self.title)

class WorkReservation(models.Model):
    proto =                 models.ForeignKey('ProtoHit')
    foreign_id =            models.IntegerField(default = 0)
    payload =               models.TextField(blank = True)
    start_time =            models.DecimalField(max_digits = 19, decimal_places = 3, db_index = True)
    assignments =           models.IntegerField()
    invoked =               models.BooleanField(default = False)
    done =                  models.BooleanField(default = False)
    
    @property
    def siblings(self):
        return WorkReservation.objects.exclude(id = self.id).filter(proto = self.proto)
    
    @property
    def workers(self):
        flushTransaction() # may no longer be needed after console->cron script conversion
        timeCutoff = datetime.now() - timedelta(seconds = PING_TIMEOUT_SECONDS)
        waitingWorkers = Assignment.objects.filter( \
            event__event_type = 'waiting', \
            event__server_time__gte = unixtime(timeCutoff), \
            hit_id__reservation = self, \
            task_id = None).distinct()
        return waitingWorkers
        
    @property
    def objectify(self):
        return { \
            'id': self.id, \
            'proto': self.proto.objectify, \
            'foreignID': self.foreign_id, \
            'payload': self.payload, \
            'startTime': int(self.start_time * 1000), \
            'assignments': self.assignments, \
            'workers': len(self.workers), \
            'invoked': self.invoked, \
            'done': self.done
        }
    
    def __unicode__(self):
        status = u'Complete - ' if self.done else u'Incomplete - '
        status2 = u'Invoked - ' if self.invoked else u'Waiting - '
        return status + status2 + unicode(self.proto.hit_type_id) + u':: reservation for ' + unicode(self.assignments) + u' workers with foreign id: ' + unicode(self.foreign_id)
    
class Event(models.Model):
    assignment =            models.ForeignKey('Assignment')
    detail =                models.TextField()
    client_time =           models.DecimalField(max_digits=19, decimal_places=3)
    ip =                    models.CharField(max_length=384)
    event_type =            models.CharField(max_length=60)
    server_time =           models.DecimalField(max_digits=19, decimal_places=3, db_index=True)
    user_agent =            models.CharField(max_length=600)

    def __unicode__(self):
        return unicode(self.assignment) + u': ' + self.event_type

class APIKey(models.Model):
    key =                   models.CharField(max_length=255, primary_key=True)
    revoked =               models.BooleanField()
    
    def __unicode__(self):
        return unicode('Inactive' if self.revoked else 'Active') + ' :: ' + unicode(self.key)
    
    def active(self):
        return not self.revoked
        
    @staticmethod
    def check(key):
        keys = APIKey.objects.filter(key = key)
        return len(keys) > 0 and keys[0].active()
    
    @staticmethod
    def needed():
        if(len(APIKey.objects.all()) > 0):
            return True
        else:
            return False