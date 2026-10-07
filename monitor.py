#!/usr/bin/env python3
"""Public availability only; no application credentials, accounts or provider APIs."""
import base64, datetime, json, os, subprocess, sys, tempfile, urllib.request, urllib.error
REPOSITORY='zeoneed/wkuwaj-status'
API='https://api.github.com/repos/'+REPOSITORY
MODES={'production':('production','https://wkuwaj.pl/health.php'),
       'test-failure':('test','https://wkuwaj.pl/monitor-test-inactive-20261007'),
       'test-recovery':('test','https://wkuwaj.pl/')}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def api(method,path,payload=None,missing=False):
    req=urllib.request.Request(API+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,
      headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10','User-Agent':'wkuwaj-status','Content-Type':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=15) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        if missing and e.code==404:return None
        raise RuntimeError('GitHub API request failed: HTTP '+str(e.code)) from None

def probe(mode):
    url=MODES[mode][1]
    with tempfile.TemporaryDirectory() as d:
        path=d+'/body'
        p=subprocess.run(['curl','--silent','--show-error','--proto','=https','--tlsv1.2','--connect-timeout','5','--max-time','10','--max-filesize','2097152','--output',path,'--write-out','%{http_code}',url],capture_output=True,text=True)
        body=open(path,'rb').read(2097153) if os.path.exists(path) else b''
    good=p.returncode==0 and p.stdout=='200' and (b'Wkuwaj' in body if mode=='test-recovery' else body==b'{"status":"ok"}')
    return good,{'http_status':p.stdout or '000','curl_exit':p.returncode,'url':url}

def next_state(previous,good):
    sample='up' if good else 'down';old=previous.get('sample');count=min(2,int(previous.get('count',0))+1) if old==sample else 1
    status=previous.get('status','up');transition=None
    if count==2 and status!=sample:status=sample;transition=sample
    return {'sample':sample,'count':count,'status':status,'issue_number':previous.get('issue_number')},transition

def find_issue(channel):
    marker='<!-- wkuwaj-monitor:'+channel+' -->'
    issues=api('GET','/issues?state=open&per_page=100')
    return next((x for x in issues if x.get('user',{}).get('login')=='github-actions[bot]' and marker in (x.get('body') or '')),None)

def main():
    mode=os.environ.get('PROBE_MODE') or 'production'
    if mode not in MODES or os.environ.get('GITHUB_REPOSITORY')!=REPOSITORY:raise RuntimeError('Unapproved monitor scope')
    channel,url=MODES[mode];file='/contents/state/'+channel+'.json';remote=api('GET',file,missing=True)
    previous=json.loads(base64.b64decode(remote['content'])) if remote else {'status':'up','count':0,'sample':None,'issue_number':None}
    good,result=probe(mode);new,transition=next_state(previous,good);now=datetime.datetime.now(datetime.timezone.utc).isoformat();run='https://github.com/'+REPOSITORY+'/actions/runs/'+os.environ['GITHUB_RUN_ID']
    print(json.dumps({'at':now,'channel':channel,'probe':result,'healthy':good,'consecutive':new['count'],'confirmed_status':new['status'],'transition':transition}))
    prefix='[TEST MONITORA] ' if channel=='test' else ''
    if transition=='down':
        issue=find_issue(channel)
        if not issue:issue=api('POST','/issues',{'title':prefix+'Wkuwaj.pl: alarm dostępności','body':'<!-- wkuwaj-monitor:'+channel+' -->\n@zeoneed — '+('kontrolowany test alarmu; strona nie została wyłączona.' if channel=='test' else 'Dwie kolejne kontrole publicznej sondy nie powiodły się.')+'\n\nCzas UTC: '+now+'\nAdres: '+url+'\nWynik HTTP: '+result['http_status']+'\nLog próby: '+run+'\n\nSprawdź ostatnie wdrożenie, panel hostingu i prywatny log PHP. Nie publikuj danych klientów ani kluczy.'})
        new['issue_number']=issue['number']
    elif transition=='up':
        issue=find_issue(channel)
        if issue:
            api('POST','/issues/'+str(issue['number'])+'/comments',{'body':'@zeoneed — '+prefix+'dwie kolejne kontrole zakończyły się poprawnie.\n\nCzas UTC: '+now+'\nLog: '+run})
            api('PATCH','/issues/'+str(issue['number']),{'state':'closed','state_reason':'completed'})
        new['issue_number']=None
    # Persist streak/status only on a change, plus a monthly maintenance marker.
    # No commit and no notification for every unchanged successful/down probe.
    new['maintenance_month']=now[:7]
    if new!=previous:
        payload={'message':'Update '+channel+' availability state','content':base64.b64encode((json.dumps(new,indent=2)+'\n').encode()).decode(),'branch':'main'}
        if remote:payload['sha']=remote['sha']
        api('PUT',file,payload)
    summary='HTTP '+result['http_status']+'; confirmed '+new['status']+'; '+str(new['count'])+' consecutive '+new['sample']+' probes.'
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary+'\n')

if __name__=='__main__':
    if '--self-test' in sys.argv:
        s={'status':'up','count':0,'sample':None,'issue_number':None};transitions=[]
        for sample in [False,False,False,True,False,True,True,True]:s,t=next_state(s,sample);transitions.append(t)
        assert transitions==[None,'down',None,None,None,None,'up',None]
        assert s['status']=='up' and s['count']==2
        print('Passed: two consecutive failures/recoveries; unchanged state stays quiet; interruption resets streak.')
    else:
        try:main()
        except Exception as e:print('Monitor execution failed: '+type(e).__name__,file=sys.stderr);sys.exit(1)
