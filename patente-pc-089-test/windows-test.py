import base64, hashlib, json, pathlib, zlib, os, shutil, subprocess, time, urllib.request, urllib.error, ssl, socket, re, threading, functools, http.server, tempfile, uuid, io
from PIL import Image, ImageDraw

workspace=pathlib.Path.cwd()
stage=workspace/'patente-pc-089-test'
recovery=workspace/'recovery'
m=json.loads((stage/'skeleton.json').read_text())
raw=bytearray(zlib.decompress(base64.b64decode(''.join(f.read_text().strip() for f in sorted(stage.glob('part-*.b64'))),validate=True)))
assert len(raw)==m['size']
for x in m['ops']:
    b=(recovery/x['path']).read_bytes()
    assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
    assert not any(raw[x['offset']:x['offset']+x['size']])
    raw[x['offset']:x['offset']+x['size']]=b
assert hashlib.sha256(raw).hexdigest()==m['sha256']
manifest=json.loads((stage/'test-update.json').read_text())
report={'candidate_sha256':m['sha256'],'candidate_size':len(raw),'checks':{}}
def mark(k,v=True):
    report['checks'][k]=v
    print(k,v,flush=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sandbox=pathlib.Path(tempfile.mkdtemp(prefix='patente-ci-'))
feed=sandbox/'feed';feed.mkdir()
(feed/manifest['file']).write_bytes(raw)
(feed/'update.json').write_text(json.dumps(manifest),encoding='utf-8')
old=recovery/'reference-088.exe'
assert digest(old)=='dd20110d3899d49519d0b7cfd92c133f8500f937e36ddf2fb5f9bc906ff71b62'
root=sandbox/'local'/'Jorrob'/'PatenteStudioPWA'
target=root/'Programma'/'PatenteStudio.exe'
target.parent.mkdir(parents=True)
shutil.copyfile(old,target)
env=os.environ.copy()
env['LOCALAPPDATA']=str(sandbox/'local')
env['PATENTE_STUDIO_UPDATE_FEED']='http://127.0.0.1:18889/update.json'
env['PATENTE_STUDIO_LAN_IP']='192.168.10.25'
env['NO_PROXY']='127.0.0.1,localhost'
export=sandbox/'RINNOVO PATENTE FITTIZIO';export.mkdir()
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',18889),functools.partial(QuietHandler,directory=str(feed)))
threading.Thread(target=server.serve_forever,daemon=True).start()
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def call(path,token=None,body=None,timeout=10):
    headers={}
    if token:headers['Authorization']='Bearer '+token
    if body is not None:headers['Content-Type']='application/json'
    req=urllib.request.Request('http://127.0.0.1:18885'+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
    with opener.open(req,timeout=timeout) as r:return json.load(r)
def wait_health(version,seconds=65,ready=False):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            h=call('/api/health',timeout=2)
            if h.get('version')==version and (not ready or h.get('desktop_window_ready') is True):return h
        except Exception:pass
        time.sleep(.5)
    raise RuntimeError('No verified health for '+version)
def jpeg(img):
    buf=io.BytesIO();img.save(buf,format='JPEG',quality=90);return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
def pinned_peer(pin):
    # Local synthetic fixture only: check DER pin exactly; real Android also verifies IP SAN and validity.
    c=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);c.check_hostname=False;c.verify_mode=ssl.CERT_NONE
    with socket.create_connection(('127.0.0.1',18886),timeout=5) as raw:
        with c.wrap_socket(raw,server_hostname='192.168.10.25') as tls:
            assert hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()==pin
def pin_of(q):return re.search(r'&pin=([a-f0-9]{64})$',q['url']).group(1)
def make_job():
    p=Image.new('RGB',(260,315),(240,240,240));d=ImageDraw.Draw(p);d.ellipse((64,45,196,250),fill=(160,120,100));d.ellipse((92,110,110,128),fill='black');d.ellipse((148,110,166,128),fill='black')
    s=Image.new('RGB',(236,47),'white');d=ImageDraw.Draw(s);d.line([(15,30),(38,8),(60,35),(90,12),(115,32),(145,9),(185,28),(220,20)],fill='black',width=3)
    return dict(name='FITTIZIO',surname='COLLAUDO',photo=jpeg(p),signature=jpeg(s),icao_confirmed=True,client_request_id=str(uuid.uuid4()))
proc=None
try:
    proc=subprocess.Popen([str(target),'--installed'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    wait_health('0.8.8')
    config=json.loads((root/'config.json').read_text())
    admin=config['admin_key'];capture=config['capture_key'];assert admin and capture
    call('/api/config',admin,{'export_dir':str(export)})
    config0=(root/'config.json').read_bytes()
    q0=call('/api/pairing',admin)
    pin0=pin_of(q0);pinned_peer(pin0)
    assert capture in q0['url']
    job=make_job()
    created=call('/api/jobs',capture,job)
    oldfiles={p.name:digest(p) for p in export.glob('*.jpg')}
    assert len(oldfiles)==2
    archive0=(root/'archive.json').read_bytes()
    mark('original_088_config_archive_qr_and_capture')
    update=call('/api/update',admin)
    assert update.get('available') and update.get('version')=='0.8.9',str(update.get('reason','unavailable'))
    mark('original_088_sees_signed_089')
    install=call('/api/update/install',admin,{},timeout=45)
    mark('original_088_installer_requested')
    wait_health('0.8.9',seconds=100,ready=True)
    time.sleep(3)
    wait_health('0.8.9',seconds=10,ready=True)
    assert digest(target)==m['sha256']
    mark('actual_windows_update_and_edge_window')
    assert (root/'config.json').read_bytes()==config0
    assert (root/'archive.json').read_bytes()==archive0
    assert {p.name:digest(p) for p in export.glob('*.jpg')}==oldfiles
    cfg=call('/api/config',admin);assert cfg['export_dir']==str(export) and cfg['version']=='0.8.9' and not cfg.get('collaudo')
    q=call('/api/pairing',admin);assert q['url']==q0['url'];pinned_peer(pin0)
    mark('configuration_archive_files_and_tablet_pin_preserved')
    # Existing credentials still work; exercise acquisition path after migration.
    job2=make_job();job2['name']='SECONDO'
    call('/api/jobs',capture,job2)
    assert len(list(export.glob('*.jpg')))==4
    mark('capture_after_update')
    assert any(digest(p)==digest(old) for p in target.parent.glob('PatenteStudio.exe.old-*'))
    mark('rollback_executable_preserved')
    latest=call('/api/update',admin)
    assert not latest.get('available')
    mark('no_duplicate_update')
    report['passed']=True
finally:
    report.setdefault('passed',False)
    (workspace/'windows-update-report.json').write_text(json.dumps(report,indent=2))
    server.shutdown()
    # Hosted test runner only: no user processes/data.
    if proc and proc.poll() is None:proc.kill()
    subprocess.run(['taskkill','/F','/IM','PatenteStudio.exe'],capture_output=True,check=False)
