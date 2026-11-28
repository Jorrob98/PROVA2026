"""Generate 1.0.2 from the exact published 1.0.1 source. Fail on any unexpected source."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
java=root/'app/src/main/java/it/jorrob/patentetab'
def edit(path, pairs):
    s=path.read_text(encoding='utf-8')
    for old,new in pairs:
        assert s.count(old)==1, f'{path.name}: unexpected match count for {old[:80]}'
        s=s.replace(old,new,1)
    path.write_text(s,encoding='utf-8')
edit(root/'app/build.gradle', [('versionCode 2; versionName \'1.0.1\'','versionCode 3; versionName \'1.0.2\'')])
edit(java/'TabletUpdates.java',[
('private final Activity a;private boolean busy, closed;', 'private final Activity a;private boolean busy; private volatile boolean closed, cancelled;'),
('return "1.0.1";','return "1.0.2";'),
('void check(){if(busy)return;busy=true;progress=new ProgressDialog(a);','void check(){check(false,()->true);}\n void check(boolean silent,java.util.function.BooleanSupplier available){if(busy||closed)return;busy=true;if(!silent){progress=new ProgressDialog(a);'),
('progress.setCancelable(false);progress.show();new Thread(()->{try{JSONObject m=manifest();','progress.setCancelable(false);progress.show();}new Thread(()->{try{JSONObject m=manifest();'),
('if(code<=current){message("Patente Studio",','if(!available.getAsBoolean())return;if(code<=current){if(!silent)message("Patente Studio",'),
('catch(Exception e){fail("Controllo non riuscito. Verifica la connessione Internet.");}}).start();}', 'catch(Exception e){if(silent)ui(()->{dismiss();busy=false;});else fail("Controllo non riuscito. Verifica la connessione Internet.");}}).start();}'),
('private void download(String v,String name,String sha,long size,int code){if(busy)return;busy=true;', 'private void download(String v,String name,String sha,long size,int code){if(busy||closed)return;busy=true;cancelled=false;'),
('progress.setMax(100);progress.setCancelable(false);progress.show();', 'progress.setMax(100);progress.setCancelable(false);progress.setButton(DialogInterface.BUTTON_NEGATIVE,"Annulla",(d,w)->cancelled=true);progress.show();'),
('if(total>size||closed)', 'if(total>size||closed||cancelled)'),
('if(total!=size||!hex', 'if(cancelled||closed)throw new IOException("Download interrotto");if(total!=size||!hex'),
('ui(()->{dismiss();busy=false;pending=apk;install();});', 'ui(()->{dismiss();busy=false;if(cancelled){apk.delete();return;}pending=apk;install();});'),
('if(f!=null)f.delete();fail(e instanceof SecurityException?', 'if(f!=null)f.delete();if(cancelled)ui(()->{dismiss();busy=false;});else fail(e instanceof SecurityException?'),
('void close(){closed=true;dismiss();}', 'void close(){closed=true;cancelled=true;dismiss();}')
])
edit(java/'MainActivity.java',[
('private boolean failureDialog=false;', 'private boolean failureDialog=false, retrying=false;'),
('showHome();}\n private void shell()', 'cleanCaptureCache();showHome();new Handler(Looper.getMainLooper()).postDelayed(()->{if(!isFinishing()&&active==null)updates.check(true,()->active==null&&!isFinishing());},1200);}\n private void cleanCaptureCache(){File dir=new File(getCacheDir(),"capture");File[] files=dir.listFiles();if(files!=null)for(File f:files)if(f.isFile())f.delete();}\n private void shell()'),
('private void connectionError(WebView w,Pc pc){', 'private void probeConnection(WebView w,Pc pc){if(retrying||web!=w||active!=pc)return;retrying=true;int seq=generation;new Thread(()->{boolean ok=false;try{preflight(pc);ok=true;}catch(Exception ignored){}final boolean reachable=ok;runOnUiThread(()->{retrying=false;if(seq!=generation||web!=w||active!=pc||isFinishing())return;if(reachable)Toast.makeText(this,"PC raggiungibile. Prova a reinviare dalla pratica aperta.",Toast.LENGTH_LONG).show();else Toast.makeText(this,"PC non raggiungibile. La pratica resta aperta; verifica la rete.",Toast.LENGTH_LONG).show();});}).start();}\n private void connectionError(WebView w,Pc pc){'),
('.setNegativeButton("Resta qui",(d,k)->failureDialog=false).setPositiveButton("Ricollega",(d,k)->{failureDialog=false;connect(pc);}).setNeutralButton("Postazioni",(d,k)->{failureDialog=false;showHome();})', '.setNegativeButton("Resta qui",(d,k)->failureDialog=false).setPositiveButton("Verifica rete",(d,k)->{failureDialog=false;probeConnection(w,pc);}).setNeutralButton("Ricarica",(d,k)->{failureDialog=false;new AlertDialog.Builder(this).setTitle("Ricaricare la pratica?").setMessage("Foto e firma non inviate potrebbero andare perse. Ricarica solo se necessario.").setNegativeButton("Annulla",null).setPositiveButton("Ricarica",(a,b)->connect(pc)).show();})'),
('chooser.onReceiveValue(u==null?null:new Uri[]{u});chooser=null;photoUri=null;', 'chooser.onReceiveValue(u==null?null:new Uri[]{u});chooser=null;photoUri=null;if(u==null&&photoFile!=null){photoFile.delete();photoFile=null;}'),
('if(req==303){if(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED)captureNative();','if(req==303){if(chooser!=null&&verified&&grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED)captureNative();'),
('@Override protected void onDestroy(){generation++;verified=false;stopWeb();', '@Override protected void onResume(){super.onResume();if(updates!=null)updates.resume();}\n @Override protected void onDestroy(){generation++;verified=false;if(updates!=null)updates.close();stopWeb();')
])
print("Patente Studio 1.0.2 source prepared")
