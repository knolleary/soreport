from django.views.generic.simple import direct_to_template
from django.conf.urls import patterns, include, url
import os

urlpatterns = patterns('',
    (r'^$','soreport.views.sample'),
    (r'^edition/?$','soreport.views.edition'),
    (r'^sample/?$','soreport.views.sample'),
    (r'^validate_config/?$','soreport.views.validate_config'),
    (r'^configure/?$','soreport.views.configure'),
    (r'^return/?$','soreport.views.oauth_return'),

    (r'^meta.json$',direct_to_template,{'template':'soreport/meta.json'}),
    (r'^icon.png$', 'django.views.static.serve',{'path': 'icon.png','document_root': os.path.dirname(__file__),}),
    (r'^static/(?P<path>.*)$','django.views.static.serve',{'document_root':os.path.dirname(__file__)+"/static"}),
)
