from django.conf import settings
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import hashlib
import datetime
import cStringIO,gzip
import httplib2,urllib,urlparse
import json
import time

def render(request,context):
  t = loader.get_template('soreport/index.html')
  c = RequestContext(request,context)
  
  zbuf = cStringIO.StringIO()
  zfile = gzip.GzipFile(mode='wb',compresslevel=6,fileobj=zbuf)
  zfile.write(t.render(c).encode('utf-8'))
  zfile.close()
  
  cc = zbuf.getvalue()
  response = HttpResponse(cc)
  response['Content-Encoding'] = 'gzip'
  response['Content-Length'] = str(len(cc))
 
  m = hashlib.md5()
  m.update(datetime.datetime.utcnow().isoformat())
  response['ETag'] = '"'+m.hexdigest()+'"'
  return response
  
@csrf_exempt
def validate_config(request):
  # Cheat a bit; any config is valid as we will default the size
  # if not specified
  return HttpResponse('{"valid":true}')
  
def oauth_return(request):
  url = "https://stackexchange.com/oauth/access_token"
  params = urllib.urlencode({'client_id': settings.SOREPORT_CLIENT_ID, 'client_secret': settings.SOREPORT_CLIENT_SECRET, 'code':request.GET['code'],'redirect_uri':'http://kahiti.knolleary.net/soreport/return'})
  headers = {'Content-type': 'application/x-www-form-urlencoded'}
  resp,content = httplib2.Http().request(url,"POST",headers=headers, body=params)
  if resp['status'] == '200':
    v=urlparse.parse_qs(content)
    access_token=v['access_token'][0]
    if 'bergcloud_return_url' in request.COOKIES:
      return_url = request.COOKIES['bergcloud_return_url']
      return HttpResponseRedirect("%s?config[access_token]=%s"%(return_url,access_token))
    else:
      return HttpResponse("Missing return_url cookie")
  else:
    return HttpResponse("Unexpected response from StackExchange:"+content)
  
def configure(request):
  return_url = request.GET['return_url']
  response = HttpResponseRedirect("https://stackexchange.com/oauth?client_id=%s&scope=no_expiry,private_info,read_inbox&redirect_uri=%s"%(settings.SOREPORT_CLIENT_ID,"http://kahiti.knolleary.net/soreport/return"))
  response.set_cookie("bergcloud_return_url",return_url,expires=datetime.datetime.utcnow()+datetime.timedelta(hours=4))
  return response

def sample(request):
  context = {
     'display_name':'A User',
     'badge_counts':{'bronze':10,'silver':30,'gold':2},
     'reputation':2086,
     'repevents':[
        {'date':0,'rep':10},
        {'date':86400*1,'rep':0},
        {'date':86400*2,'rep':10},
        {'date':86400*3,'rep':0},
        {'date':86400*4,'rep':50},
        {'date':86400*5,'rep':10},
        {'date':86400*6,'rep':30},
        {'date':86400*7,'rep':0},
        {'date':86400*8,'rep':0},
        {'date':86400*9,'rep':10},
        {'date':86400*10,'rep':20},
        {'date':86400*11,'rep':0},
        {'date':86400*12,'rep':10},
        {'date':86400*13,'rep':35}
     ],
     'history':[
        {'rep': 25, 'items': [{'c': [1], 'label': u'up_votes'}, {'c': [1], 'label': u'accepts'}], 'post_type': u'answer', 'title': u'Onewire temperatures to MQTT broker server'},
        {'rep': 10, 'items': [{'c': [1], 'label': u'up_votes'}], 'post_type': u'answer', 'title': u'Regex expression for Apostrophe'}
     ],
     'notifications':[
        {'body': u'You\'ve earned the "Informed" badge.', 'type': u'badge_earned'},
        {'body': u"Congrats, you've gained the privilege &ndash; vote down", 'type': u'new_privilege'}
     ]
  }
  return render(request,context);
  
def edition(request):
  context = get_so_data(request)
  if len(context['history']) == 0 and len(context['notifications']) == 0:
    return HttpResponse(status=204)
  return render(request,context)


def get_so_data(request):
  context = {}
  
  now = int(time.mktime(time.gmtime()))
  weekago = now-(13*60*60*24)
  yesterday = now-(1*60*60*24)
  http=httplib2.Http()
  
  token = request.GET['access_token']
    
  key = settings.SOREPORT_KEY
  
  
  def get(baseurl):
    fill=""
    if "?" in baseurl:
      if baseurl[-1] != "?":
        fill="&"
    else:
      fill="?"
      
    url="https://api.stackexchange.com/2.1%s%ssite=stackoverflow&key=%s&access_token=%s"%(baseurl,fill,key,token)
    resp,content=http.request(url)
    return json.loads(content)
  
  
  userdata = get("/me")

  if len(userdata['items']) == 0:
    context['notifications'] = []
    context['history'] = []
    return context
 
  user = get("/me")['items'][0]
  
  context['display_name'] = user['display_name']
  context['badge_counts'] = user['badge_counts']
  context['reputation'] = user['reputation']
  context['profile_image'] = user['profile_image']
  
  posts = {}
  
  repevents = {}
  
  # How fragile is referring to a filter like this? 
  reps = get("/me/reputation?fromdate="+str(int(weekago))+"&filter=!9j_cPdEGT")
  for r in reps['items']:
    if int(r['on_date']) > yesterday:
      pid = str(r['post_id'])
      if pid not in posts:
        posts[pid] = {'title':r['title'],'post_type':r['post_type'],'changes':{},'rep':0}
      
      if r['vote_type'] not in posts[pid]['changes']:
        posts[pid]['changes'][r['vote_type']] = []
      posts[pid]['changes'][r['vote_type']].append(1)
      if 'reputation_change' in r:
        posts[pid]['rep'] += r['reputation_change']
    ondate = time.gmtime(r['on_date'])
    midnight = time.mktime((ondate.tm_year,ondate.tm_mon,ondate.tm_mday,0,0,0,ondate.tm_wday,ondate.tm_yday,ondate.tm_isdst))
    dateid = str(int(midnight))
    if dateid not in repevents:
      repevents[dateid] = 0
    if 'reputation_change' in r:
      repevents[dateid] += r['reputation_change']
  weekagotime = time.gmtime(weekago)
  weekagomidnight = int(time.mktime((weekagotime.tm_year,weekagotime.tm_mon,weekagotime.tm_mday,0,0,0,weekagotime.tm_wday,weekagotime.tm_yday,weekagotime.tm_isdst)))
  while (weekagomidnight < now):
    if (str(weekagomidnight) not in repevents):
      repevents[str(weekagomidnight)] = 0
    weekagomidnight += 60*60*24
  
  context['repevents'] = [ {'date':k,'rep':repevents[k]} for k in repevents  ]
  context['repevents'].sort(key=lambda x: int(x['date']))

  history = []
  for p in posts:
    posts[p]['items'] = []
    for c in posts[p]['changes']:
      posts[p]['items'].append({'label':c,'c':posts[p]['changes'][c]})
    del posts[p]['changes']
    history.append(posts[p])
  
  history.sort(key=lambda x: x['rep'],reverse=True)
  context['history'] = history
  context['morenotifications'] = 0
  context['morehistory'] = 0
  
  ans = get("/me/notifications")['items']
  context['notifications'] = []
  for a in ans:
    if int(a['creation_date']) > yesterday:
      body = a['body']
      if (a['notification_type'] == 'new_privilege'):
        body = body[0:body.index('<')-1]
      context['notifications'].append({"type":a['notification_type'],"body":body})

  num_history = len(context['history'])
  num_notif = len(context['notifications'])
  
  if num_history > 5:
    context['history'] = context['history'][0:5]
    context['morehistory'] = num_history-5
  
  max_notifications = 8-len(context['history'])
  if num_notif > max_notifications:
    context['notifications'] = context['notifications'][0:max_notifications]
    context['morenotifications'] = num_notif-max_notifications
  print context['notifications']   
  context['more'] = context['morenotifications'] + context['morehistory']
  return context
  
  
