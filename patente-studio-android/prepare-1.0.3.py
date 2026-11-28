"""Apply tablet-only improvements on top of the verified 1.0.2 source."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
java=root/'app/src/main/java/it/jorrob/patentetab'
def edit(path,pairs):
    s=path.read_text(encoding='utf-8')
    for a,b in pairs:
        assert s.count(a)==1, f'{path.name}: missing/ambiguous {a[:90]}'
        s=s.replace(a,b,1)
    path.write_text(s,encoding='utf-8')
edit(root/'app/build.gradle',[("versionCode 3; versionName '1.0.2'","versionCode 4; versionName '1.0.3'")])
edit(java/'TabletUpdates.java',[('return "1.0.2";','return "1.0.3";')])
p=java/'MainActivity.java'
edit(p,[
('private static final int GREEN=0xff0a4347, BACK=0xfff3f8f5;', 'private static final int GREEN=0xff153c70, BACK=0xffedf2f8;\n private final java.util.concurrent.ExecutorService probes=java.util.concurrent.Executors.newFixedThreadPool(3);\n private final Handler monitor=new Handler(Looper.getMainLooper()); private boolean foreground=false; private int refreshId=0;'),
('private void persist(){prefs.edit().putString("pcs",saved.toString()).apply();}', '''private void persist(){try{String cipher=PcVault.encrypt(saved.toString());prefs.edit().putString("pcs-secure",cipher).remove("pcs").apply();}catch(Exception e){Toast.makeText(this,"Impossibile salvare le postazioni in modo sicuro.",Toast.LENGTH_LONG).show();}}
 private void loadSaved(){try{String encrypted=prefs.getString("pcs-secure",null);if(encrypted!=null)saved=new JSONObject(PcVault.decrypt(encrypted));else{saved=new JSONObject(prefs.getString("pcs","{}"));if(saved.length()>0)persist();}}catch(Exception e){saved=new JSONObject();Toast.makeText(this,"Archivio postazioni non accessibile: ripeti il QR.",Toast.LENGTH_LONG).show();}}
 private String pcName(Pc pc){JSONObject o=saved.optJSONObject(pc.host);return o==null?"PC "+pc.host:o.optString("name","PC "+pc.host);}
 private void rename(Pc pc){EditText field=new EditText(this);field.setSingleLine(true);field.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(40)});field.setText(pcName(pc));new AlertDialog.Builder(this).setTitle("Nome postazione").setView(field).setNegativeButton("Annulla",null).setPositiveButton("Salva",(d,w)->{String n=field.getText().toString().trim();try{JSONObject o=saved.optJSONObject(pc.host);if(o!=null){o.put("name",n.isEmpty()?"PC "+pc.host:n);persist();showHome();}}catch(Exception ignored){}}).show();}
 private final java.util.Map<Pc,TextView> indicators=new java.util.LinkedHashMap<>();
 private final Runnable refreshTask=new Runnable(){public void run(){if(!foreground||active!=null||isFinishing())return;int id=++refreshId;for(java.util.Map.Entry<Pc,TextView> entry:indicators.entrySet()){Pc pc=entry.getKey();TextView view=entry.getValue();probes.execute(()->{boolean ok=false;try{preflight(pc);ok=true;}catch(Exception ignored){}final boolean reachable=ok;runOnUiThread(()->{if(id!=refreshId||!foreground||active!=null||isFinishing())return;view.setText(reachable?"Disponibile":"Non raggiungibile / QR da verificare");view.setTextColor(reachable?0xff12794c:0xff9a4e19);});});}monitor.postDelayed(this,30000);}};
 private void stopMonitor(){monitor.removeCallbacks(refreshTask);refreshId++;}
 private void startMonitor(){stopMonitor();if(foreground&&active==null&&!isFinishing())monitor.post(refreshTask);}
 private void diagnostics(){android.net.ConnectivityManager cm=(android.net.ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);android.net.Network net=cm==null?null:cm.getActiveNetwork();android.net.NetworkCapabilities caps=net==null?null:cm.getNetworkCapabilities(net);String wifi=caps!=null&&caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI)?"Connesso":"Non rilevato";new AlertDialog.Builder(this).setTitle("Diagnostica").setMessage("Versione: "+updates.version()+"\\nWi-Fi: "+wifi+"\\nPostazioni: "+saved.length()+"\\nFotocamera: "+(getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)?"Presente":"Non rilevata")+"\\nSpazio cache disponibile: "+(getCacheDir().getUsableSpace()/1048576)+" MB\\nI controlli non registrano dati dei clienti.").setPositiveButton("OK",null).show();}
'''),
('try{saved=new JSONObject(prefs.getString("pcs","{}"));}catch(Exception ignored){} cleanCaptureCache();','loadSaved(); cleanCaptureCache();'),
('private void showHome(){generation++;','private void showHome(){stopMonitor();indicators.clear();generation++;'),
('row.addView(button("PC "+host,()->connect(pc)),new LinearLayout.LayoutParams(0,-2,1));','LinearLayout details=new LinearLayout(this);details.setOrientation(LinearLayout.VERTICAL);details.addView(button(pcName(pc),()->connect(pc)));TextView availability=label("Verifica connessione…",12);details.addView(availability);indicators.put(pc,availability);row.addView(details,new LinearLayout.LayoutParams(0,-2,1));row.addView(button("Rinomina",()->rename(pc)));'),
('panel.addView(button("Controlla aggiornamenti",()->updates.check()));','panel.addView(button("Diagnostica",this::diagnostics));panel.addView(button("Controlla aggiornamenti",()->updates.check()));'),
('14));}\n private static boolean lanHost','14));startMonitor();}\n private static boolean lanHost'),
('private void connect(Pc pc){int seq=++generation;','private void connect(Pc pc){stopMonitor();int seq=++generation;'),
('saved.put(pc.host,pc.json());persist();','String name=pcName(pc);saved.put(pc.host,pc.json().put("name",name));persist();'),
('@Override protected void onResume(){super.onResume();if(updates!=null)updates.resume();}', '@Override protected void onResume(){super.onResume();foreground=true;if(updates!=null)updates.resume();startMonitor();}\n @Override protected void onPause(){foreground=false;stopMonitor();super.onPause();}'),
('@Override protected void onDestroy(){generation++;','@Override protected void onDestroy(){foreground=false;stopMonitor();probes.shutdownNow();generation++;')
])
edit(root/'app/src/main/AndroidManifest.xml',[('<uses-permission android:name="android.permission.INTERNET" />','<uses-permission android:name="android.permission.INTERNET" />\n <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />')])
(java/'PcVault.java').write_text('''package it.jorrob.patentetab;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.security.KeyStore;
import java.nio.charset.StandardCharsets;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
final class PcVault {
 private static final String ALIAS="patente-studio-pc-v1";
 private static synchronized SecretKey key() throws Exception {
  KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
  if(!ks.containsAlias(ALIAS)){
   KeyGenerator kg=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
   kg.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());kg.generateKey();
  }
  return (SecretKey)ks.getKey(ALIAS,null);
 }
 static String encrypt(String value)throws Exception{
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());
  return Base64.encodeToString(c.getIV(),Base64.NO_WRAP)+"."+Base64.encodeToString(c.doFinal(value.getBytes(StandardCharsets.UTF_8)),Base64.NO_WRAP);
 }
 static String decrypt(String value)throws Exception{
  String[] p=value.split("\\\\.",-1);if(p.length!=2)throw new IllegalArgumentException("Invalid vault");
  Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(p[0],Base64.NO_WRAP)));
  return new String(c.doFinal(Base64.decode(p[1],Base64.NO_WRAP)),StandardCharsets.UTF_8);
 }
}
''',encoding='utf-8')
print("Patente Studio 1.0.3 tablet source prepared")


# Additional stability and recovery hardening (on-device verification still required).
p=java/'MainActivity.java'
s=p.read_text(encoding='utf-8')
def once(a,b):
    global s
    assert s.count(a)==1, a[:80]
    s=s.replace(a,b,1)
once('prefs.edit().putString("pcs-secure",cipher).remove("pcs").apply();','String prior=prefs.getString("pcs-secure",null);SharedPreferences.Editor editor=prefs.edit();if(prior!=null)editor.putString("pcs-secure-previous",prior);if(!editor.putString("pcs-secure",cipher).remove("pcs").commit())throw new IOException("Impostazioni non salvate");')
once('saved=new JSONObject();Toast.makeText(this,"Archivio postazioni non accessibile: ripeti il QR.",Toast.LENGTH_LONG).show();','try{String previous=prefs.getString("pcs-secure-previous",null);if(previous==null)throw new IOException();saved=new JSONObject(PcVault.decrypt(previous));if(!prefs.edit().putString("pcs-secure",previous).commit())throw new IOException();Toast.makeText(this,"Postazioni recuperate dalla copia precedente.",Toast.LENGTH_LONG).show();}catch(Exception ignored){saved=new JSONObject();Toast.makeText(this,"Archivio postazioni non accessibile: ripeti il QR.",Toast.LENGTH_LONG).show();}')
once('boolean ok=false;try{preflight(pc);ok=true;}catch(Exception ignored){}final boolean reachable=ok;runOnUiThread(()->{if(id!=refreshId','long begin=SystemClock.elapsedRealtime();boolean ok=false;try{preflight(pc);ok=true;}catch(Exception ignored){}final long elapsed=SystemClock.elapsedRealtime()-begin;final boolean reachable=ok;runOnUiThread(()->{if(id!=refreshId')
once('view.setText(reachable?"Disponibile":"Non raggiungibile / QR da verificare");','view.setText(reachable?"Disponibile • "+elapsed+" ms (verifica PC)":"Non raggiungibile / QR da verificare");')
once('new AlertDialog.Builder(this).setTitle("Diagnostica").setMessage("Versione: "+updates.version()', 'String report="Versione: "+updates.version()')
once('+" MB\\nI controlli non registrano dati dei clienti.").setPositiveButton("OK",null).show();}', '+" MB\\nI controlli non registrano dati dei clienti.";new AlertDialog.Builder(this).setTitle("Diagnostica").setMessage(report).setNeutralButton("Esporta",(d,w)->{Intent share=new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,report);startActivity(Intent.createChooser(share,"Esporta diagnostica"));}).setPositiveButton("OK",null).show();}')
once('private void captureNative(){try{File dir=', 'private void captureNative(){try{if(getCacheDir().getUsableSpace()<32L*1024*1024){cancelChooser();new AlertDialog.Builder(this).setMessage("Spazio libero insufficiente per acquisire la fotografia. Libera memoria sul tablet.").setPositiveButton("OK",null).show();return;}File dir=')
once('panel.addView(button("Controlla aggiornamenti",()->updates.check()));','panel.addView(button("Controlla aggiornamenti",()->updates.check(false,()->active==null&&!isFinishing())));')
once('if(!APP_ID.equals(h.optString("app_id")))throw new IOException("Non è un PC Patente Studio");','if(!APP_ID.equals(h.optString("app_id")))throw new IOException("Non è un PC Patente Studio");String ver=h.optString("version","");if(ver.matches("[0-9]{1,5}\\\\.[0-9]{1,5}\\\\.[0-9]{1,5}")){String[] v=ver.split("\\\\.");if(Integer.parseInt(v[0])==0&&(Integer.parseInt(v[1])<8||(Integer.parseInt(v[1])==8&&Integer.parseInt(v[2])<8)))throw new IOException("Aggiorna Patente Studio PC alla 0.8.8 o successiva");}')
once('web.loadUrl(pc.origin()+"/#pair="+pc.token);','WebView opened=web;int current=generation;new Handler(Looper.getMainLooper()).postDelayed(()->{if(generation==current&&web==opened&&active==pc&&!isFinishing()&&opened.getProgress()<100){Toast.makeText(this,"Caricamento lento. Verifica Wi-Fi e PC; la schermata non viene ricaricata automaticamente.",Toast.LENGTH_LONG).show();}},18000);web.loadUrl(pc.origin()+"/#pair="+pc.token);')
p.write_text(s,encoding='utf-8')
edit(java/'TabletUpdates.java',[
('if(busy||closed)return;busy=true;cancelled=false;', 'if(busy||closed)return;if(a.getCacheDir().getUsableSpace()<size+32L*1024*1024){message("Aggiornamento","Spazio libero insufficiente. Libera memoria e riprova.");return;}busy=true;cancelled=false;'),
('.setPositiveButton("Installa",(d,w)->download(v,name,sha,size,code))','.setPositiveButton("Installa",(d,w)->{if(available.getAsBoolean())download(v,name,sha,size,code);})')
])
p=root/'app/src/main/res/values/styles.xml'
s=p.read_text(encoding='utf-8').replace('#0A6268','#23538E').replace('#0A4347','#153C70')
p.write_text(s,encoding='utf-8')
print("Additional tablet stability changes prepared")


# Origin-scoped encrypted draft storage; used only by the coordinated PC web client.
edit(root/'app/build.gradle',[("implementation 'androidx.core:core:1.13.1'","implementation 'androidx.core:core:1.13.1'\n implementation 'androidx.webkit:webkit:1.12.1'")])
(java/'DraftVault.java').write_text('''package it.jorrob.patentetab;

import android.content.Context;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import org.json.JSONObject;

final class DraftVault {
 private static final int MAX=12*1024*1024;
 private final AtomicFile file;
 private final String scope;
 DraftVault(Context context,String token)throws Exception {
  byte[] hash=MessageDigest.getInstance("SHA-256").digest(("patente-draft-v1:"+token).getBytes(StandardCharsets.UTF_8));
  StringBuilder id=new StringBuilder();for(byte b:hash)id.append(String.format(Locale.ROOT,"%02x",b&255));
  scope=id.toString();
  File dir=new File(context.getNoBackupFilesDir(),"drafts");
  if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Draft storage unavailable");
  file=new AtomicFile(new File(dir,scope+".enc"));
 }
 synchronized JSONObject read()throws Exception{
  byte[] bytes;
  try(InputStream in=file.openRead();ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] buf=new byte[32768];int n;while((n=in.read(buf))!=-1){if(out.size()+n>MAX*2L)throw new IOException("Draft too large");out.write(buf,0,n);}bytes=out.toByteArray();
  }catch(FileNotFoundException e){if(file.getBaseFile().exists()||new File(file.getBaseFile().getPath()+".bak").exists())throw e;return new JSONObject().put("schema",1).put("pending",new org.json.JSONArray()).put("draft",JSONObject.NULL);}
  JSONObject envelope=new JSONObject(PcVault.decrypt(new String(bytes,StandardCharsets.UTF_8)));
  if(!scope.equals(envelope.getString("scope")))throw new SecurityException("Draft scope mismatch");
  return envelope.getJSONObject("state");
 }
 synchronized void write(JSONObject state)throws Exception{
  if(state.getInt("schema")!=1||state.getJSONArray("pending").length()>9||!state.has("draft"))throw new IOException("Invalid draft");
  byte[] plain=new JSONObject().put("scope",scope).put("state",state).toString().getBytes(StandardCharsets.UTF_8);
  if(plain.length>MAX)throw new IOException("Draft too large");
  byte[] data=PcVault.encrypt(new String(plain,StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8);
  FileOutputStream out=null;try{out=file.startWrite();out.write(data);out.getFD().sync();file.finishWrite(out);}catch(Exception e){if(out!=null)file.failWrite(out);throw e;}
 }
}
''',encoding='utf-8')
p=java/'MainActivity.java'
edit(p,[
('private final java.util.concurrent.ExecutorService probes=java.util.concurrent.Executors.newFixedThreadPool(3);','private final java.util.concurrent.ExecutorService probes=java.util.concurrent.Executors.newFixedThreadPool(3);\n private final java.util.concurrent.ExecutorService draftIO=java.util.concurrent.Executors.newSingleThreadExecutor();'),
('private void openWeb(Pc pc){body.removeAllViews();web=new WebView(this);','''private void bindDraftVault(WebView view,Pc pc){
  if(!androidx.webkit.WebViewFeature.isFeatureSupported(androidx.webkit.WebViewFeature.WEB_MESSAGE_LISTENER))return;
  try{
   DraftVault vault=new DraftVault(this,pc.token);
   androidx.webkit.WebViewCompat.addWebMessageListener(view,"PatenteDraft",Collections.singleton(pc.origin()),(sender,message,origin,mainFrame,reply)->{
    if(!mainFrame||sender!=web||active!=pc||!verified||!sameOrigin(origin.toString(),pc)||isFinishing())return;
    String raw=message.getData();if(raw==null||raw.length()>12*1024*1024)return;
    try{JSONObject req=new JSONObject(raw);String id=req.getString("id"),op=req.getString("op");if(!id.matches("[A-Za-z0-9-]{1,80}")||(!"get".equals(op)&&!"put".equals(op)))return;
     draftIO.execute(()->{JSONObject response=new JSONObject();try{response.put("id",id);if("get".equals(op))response.put("state",vault.read());else vault.write(req.getJSONObject("state"));response.put("ok",true);}catch(Exception e){try{response.put("id",id).put("ok",false).put("error","Archivio locale non disponibile");}catch(Exception ignored){}}
      runOnUiThread(()->{if(sender==web&&active==pc&&verified&&!isFinishing())try{reply.postMessage(response.toString());}catch(Exception ignored){}});
     });
    }catch(Exception ignored){}
   });
  }catch(Exception e){Toast.makeText(this,"Recupero locale non disponibile. Verifica Android System WebView.",Toast.LENGTH_LONG).show();}
 }
 private void toggleDedicated(){try{ActivityManager manager=(ActivityManager)getSystemService(ACTIVITY_SERVICE);if(manager!=null&&manager.getLockTaskModeState()!=ActivityManager.LOCK_TASK_MODE_NONE){stopLockTask();return;}new AlertDialog.Builder(this).setTitle("Tablet dedicato").setMessage("Android può fissare Patente Studio sullo schermo. Segui le istruzioni del dispositivo per attivarlo e uscire.").setNegativeButton("Annulla",null).setPositiveButton("Attiva",(d,w)->{try{startLockTask();}catch(Exception e){Toast.makeText(this,"Blocco schermo non disponibile",Toast.LENGTH_LONG).show();}}).show();}catch(Exception e){Toast.makeText(this,"Blocco schermo non disponibile",Toast.LENGTH_LONG).show();}}
 private void openWeb(Pc pc){body.removeAllViews();web=new WebView(this);bindDraftVault(web,pc);'''),
('panel.addView(button("Diagnostica",this::diagnostics));','panel.addView(button("Diagnostica",this::diagnostics));panel.addView(button("Modalità tablet dedicato",this::toggleDedicated));'),
('probes.shutdownNow();generation++;','probes.shutdownNow();draftIO.shutdown();generation++;')
])
print("Origin-restricted draft vault and Android screen pinning prepared")


# Reconnect only on temporary transport errors, never bypass a new certificate.
p=java/'MainActivity.java'
edit(p,[
('private void connect(Pc pc){stopMonitor();int seq=++generation;', '''private void connect(Pc pc){connect(pc,0);}
 private static boolean temporaryNetworkFailure(Throwable e){for(Throwable t=e;t!=null;t=t.getCause()){if(t instanceof javax.net.ssl.SSLException||t instanceof java.security.cert.CertificateException)return false;if(t instanceof java.net.ConnectException||t instanceof java.net.SocketTimeoutException||t instanceof java.net.NoRouteToHostException)return true;}return false;}
 private void saveVerifiedPc(Pc pc)throws JSONException{
  String name=pcName(pc);List<String> obsolete=new ArrayList<>();Iterator<String> it=saved.keys();
  while(it.hasNext()){String host=it.next();JSONObject obj=saved.optJSONObject(host);if(!host.equals(pc.host)&&obj!=null&&pc.token.equals(obj.optString("token"))){name=obj.optString("name",name);obsolete.add(host);}}
  for(String host:obsolete)saved.remove(host);
  saved.put(pc.host,pc.json().put("name",name));persist();
 }
 private void connect(Pc pc,int attempt){stopMonitor();int seq=++generation;'''),
('String name=pcName(pc);saved.put(pc.host,pc.json().put("name",name));persist();','saveVerifiedPc(pc);'),
('body.addView(button("Riprova",()->connect(pc)));body.addView(button("Torna alle postazioni",this::showHome));','''body.addView(button("Riprova",()->connect(pc)));body.addView(button("Torna alle postazioni",this::showHome));if(temporaryNetworkFailure(e)&&attempt<3&&foreground){int wait=5000*(1<<attempt);status.append("\\nNuovo tentativo automatico tra "+(wait/1000)+" secondi.");monitor.postDelayed(()->{if(foreground&&!isFinishing()&&seq==generation&&active==pc&&!verified)connect(pc,attempt+1);},wait);}'''),
('WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);','WebSettings s=web.getSettings();s.setUserAgentString(s.getUserAgentString()+" PatenteStudioAndroid/1.0.3");s.setJavaScriptEnabled(true);'),
('else vault.write(req.getJSONObject("state"));response.put("ok",true);','else{JSONObject snapshot=req.getJSONObject("state");vault.write(snapshot);response.put("empty",snapshot.isNull("draft")&&snapshot.getJSONArray("pending").length()==0);}response.put("ok",true);'),
('if(sender==web&&active==pc&&verified&&!isFinishing())try{reply.postMessage(response.toString());}','if(sender==web&&active==pc&&verified&&!isFinishing())try{if(response.optBoolean("ok")&&response.optBoolean("empty")&&chooser==null&&photoFile!=null){photoFile.delete();photoFile=null;photoUri=null;}reply.postMessage(response.toString());}')
])
print("Bounded reconnect and post-receipt capture cleanup prepared")


# DHCP recovery: learn the TLS public key only after a fully verified QR connection.
# UDP replies are address hints, never authorization. TLS possession + SAN + token remain mandatory.
p=java/'MainActivity.java'
edit(p,[
('String host,pin,token;\n  Pc(String host,String pin,String token){this.host=host;this.pin=pin;this.token=token;}','String host,pin,token,keyPin;\n  Pc(String host,String pin,String token){this(host,pin,token,"");}\n  Pc(String host,String pin,String token,String keyPin){this.host=host;this.pin=pin;this.token=token;this.keyPin=keyPin==null?"":keyPin;}'),
('return new JSONObject().put("pin",pin).put("token",token);','return new JSONObject().put("pin",pin).put("token",token).put("keyPin",keyPin);'),
('new Pc(host,obj.optString("pin"),obj.optString("token"))','new Pc(host,obj.optString("pin"),obj.optString("token"),obj.optString("keyPin"))'),
('private static void validateLeaf(X509Certificate c,Pc pc)throws Exception{','private static String shaHex(byte[] raw)throws Exception{StringBuilder out=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();}\n private static boolean equalPin(String a,String b){return b!=null&&b.matches("[a-f0-9]{64}")&&MessageDigest.isEqual(a.getBytes(StandardCharsets.US_ASCII),b.getBytes(StandardCharsets.US_ASCII));}\n private static void validateLeaf(X509Certificate c,Pc pc)throws Exception{'),
('if(!MessageDigest.isEqual(s.toString().getBytes(StandardCharsets.US_ASCII),pc.pin.getBytes(StandardCharsets.US_ASCII)))throw new CertificateException("Certificato diverso dal QR");','if(!equalPin(s.toString(),pc.pin)&&!equalPin(shaHex(c.getPublicKey().getEncoded()),pc.keyPin))throw new CertificateException("Identità TLS della postazione diversa dal QR");'),
('SSLSocketFactory factory,boolean auth)throws Exception','SSLSocketFactory factory,boolean auth,int timeout)throws Exception'),
('c.setConnectTimeout(6000);c.setReadTimeout(6000);','c.setConnectTimeout(timeout);c.setReadTimeout(timeout);'),
('private static void preflight(Pc pc)throws Exception{if(!lanHost(pc.host))','private static Pc preflight(Pc pc)throws Exception{return preflight(pc,6000);}\n private static Pc preflight(Pc pc,int timeout)throws Exception{final java.util.concurrent.atomic.AtomicReference<X509Certificate> leaf=new java.util.concurrent.atomic.AtomicReference<>();if(!lanHost(pc.host))'),
('validateLeaf(c[0],pc);}catch(Exception e){throw new CertificateException(e);}','validateLeaf(c[0],pc);leaf.set(c[0]);}catch(Exception e){throw new CertificateException(e);}'),
('ctx.getSocketFactory(),false);','ctx.getSocketFactory(),false,timeout);'),
('ctx.getSocketFactory(),true);','ctx.getSocketFactory(),true,timeout);'),
('if(!"capture".equals(role.optString("role")))throw new IOException("QR non autorizzato per tablet");}','if(!"capture".equals(role.optString("role")))throw new IOException("QR non autorizzato per tablet");X509Certificate cert=leaf.get();if(cert==null)throw new CertificateException("Identità della postazione non disponibile");String kp=h.optBoolean("ip_recovery",false)?shaHex(cert.getPublicKey().getEncoded()):"";return new Pc(pc.host,shaHex(cert.getEncoded()),pc.token,kp);}'),
('private void connect(Pc pc){connect(pc,0);}','''private Pc resolvePc(Pc known)throws Exception{
  try{return preflight(known);}catch(Exception initial){
   if(!known.keyPin.matches("[a-f0-9]{64}"))throw initial;
   for(String host:discoverAddresses()){
    if(host.equals(known.host))continue;
    try{Pc moved=preflight(new Pc(host,known.pin,known.token,known.keyPin),1800);if(equalPin(moved.keyPin,known.keyPin))return moved;}catch(Exception ignored){}
   }
   throw initial;
  }
 }
 private Set<String> discoverAddresses(){
  Set<String> found=new LinkedHashSet<>();
  android.net.ConnectivityManager cm=(android.net.ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
  android.net.Network network=cm==null?null:cm.getActiveNetwork();
  android.net.NetworkCapabilities cap=network==null?null:cm.getNetworkCapabilities(network);
  if(cap==null||cap.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN)||(!cap.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI)&&!cap.hasTransport(android.net.NetworkCapabilities.TRANSPORT_ETHERNET)))return found;
  android.net.LinkProperties links=cm.getLinkProperties(network);if(links==null)return found;
  try(DatagramSocket socket=new DatagramSocket()){
   network.bindSocket(socket);socket.setBroadcast(true);
   byte[] nonce=new byte[16];new java.security.SecureRandom().nextBytes(nonce);StringBuilder id=new StringBuilder();for(byte b:nonce)id.append(String.format(Locale.ROOT,"%02x",b&255));
   byte[] query=("PSDISCOVER1 "+id).getBytes(StandardCharsets.US_ASCII);
   Set<InetAddress> destinations=new LinkedHashSet<>();
   for(android.net.LinkAddress link:links.getLinkAddresses()){
    InetAddress ip=link.getAddress();int prefix=link.getPrefixLength();if(!(ip instanceof Inet4Address)||!lanHost(ip.getHostAddress())||prefix<8||prefix>30)continue;
    byte[] b=ip.getAddress();int n=((b[0]&255)<<24)|((b[1]&255)<<16)|((b[2]&255)<<8)|(b[3]&255);int broadcast=n|(-1>>>prefix);
    destinations.add(InetAddress.getByAddress(new byte[]{(byte)(broadcast>>>24),(byte)(broadcast>>>16),(byte)(broadcast>>>8),(byte)broadcast}));
   }
   if(destinations.isEmpty())return found;
   for(InetAddress dest:destinations)socket.send(new DatagramPacket(query,query.length,dest,18887));
   long until=SystemClock.elapsedRealtime()+1600;
   while(found.size()<6&&SystemClock.elapsedRealtime()<until){
    socket.setSoTimeout((int)Math.max(1,until-SystemClock.elapsedRealtime()));
    byte[] buf=new byte[128];DatagramPacket response=new DatagramPacket(buf,buf.length);
    try{socket.receive(response);}catch(SocketTimeoutException e){break;}
    String host=response.getAddress().getHostAddress();
    if(response.getPort()==18887&&lanHost(host)&&response.getLength()==query.length&&MessageDigest.isEqual(query,Arrays.copyOf(buf,response.getLength())))found.add(host);
   }
  }catch(Exception ignored){}
  return found;
 }
 private void connect(Pc pc){connect(pc,0);}'''),
('String name=pcName(pc);List<String> obsolete=new ArrayList<>();','JSONObject collision=saved.optJSONObject(pc.host);if(collision!=null&&!pc.token.equals(collision.optString("token")))return;\n  String name=pcName(pc);List<String> obsolete=new ArrayList<>();'),
('try{preflight(pc);runOnUiThread(()->{if(seq!=generation||isFinishing())return;try{saveVerifiedPc(pc);}catch(Exception ignored){}verified=true;openWeb(pc);});}','try{Pc ready=resolvePc(pc);runOnUiThread(()->{if(seq!=generation||isFinishing())return;active=ready;try{saveVerifiedPc(ready);}catch(Exception ignored){}verified=true;if(!ready.host.equals(pc.host))Toast.makeText(this,"Postazione ritrovata in sicurezza al nuovo indirizzo.",Toast.LENGTH_LONG).show();openWeb(ready);});}')
])
print("Bounded LAN discovery with previously authenticated TLS public key prepared")
