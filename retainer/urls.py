from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gettask/assignment/(?P<assignment_id>.+)$', 'retainer.gettask.getTask'),
    url(r'^retainer/gettask/assignment/(?P<assignment_id>.+)$', 'retainer.gettask.getTask'), 
    
    url(r'^ping/worker/(?P<worker_id>.+)/assignment/(?P<assignment_id>.+)/hit/(?P<hit_id>.+)/event/(?P<ping_type>.+)$', 'retainer.ping.ping'),
    url(r'^retainer/ping/worker/(?P<worker_id>.+)/assignment/(?P<assignment_id>.+)/hit/(?P<hit_id>.+)/event/(?P<ping_type>.+)$', 'retainer.ping.ping'),
    
    url(r'^puttask$', 'retainer.puttask.put_task'),
    url(r'^retainer/puttask$', 'retainer.puttask.put_task'),
    
    url(r'^putwork$', 'retainer.putwork.put_work'),
    url(r'^retainer/putwork$', 'retainer.putwork.put_work'),
    
    url(r'^putwork/done$', 'retainer.putwork.finish_work'),
    url(r'^retainer/putwork/done$', 'retainer.putwork.finish_work'),
    
    url(r'^reservation/make$', 'retainer.reservation.make'),
    url(r'^retainer/reservation/make$', 'retainer.reservation.make'),
    
    url(r'^reservation/cancel$', 'retainer.reservation.cancel'),
    url(r'^retainer/reservation/cancel$', 'retainer.reservation.cancel'),
    
    url(r'^reservation/invoke$', 'retainer.reservation.invoke'),
    url(r'^retainer/reservation/invoke$', 'retainer.reservation.invoke'),
    
    url(r'^reservation/finish$', 'retainer.reservation.finish'),
    url(r'^retainer/reservation/finish$', 'retainer.reservation.finish'),
    
    url(r'^reservation/list$', 'retainer.reservation.list'),
    url(r'^retainer/reservation/list$', 'retainer.reservation.list'),
    
    url(r'^reservation/finish/all$', 'retainer.reservation.finishAll'),
    url(r'^retainer/reservation/finish/all$', 'retainer.reservation.finishAll'),
    # Examples:
    # url(r'^$', 'retainer.views.home', name='home'),
    # url(r'^retainer/', include('retainer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^retainer/admin/', include(admin.site.urls)),
)
