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
