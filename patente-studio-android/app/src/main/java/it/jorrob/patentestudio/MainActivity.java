package it.jorrob.patentestudio;
import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;
public class MainActivity extends Activity {
 private LinearLayout root, bar;private FrameLayout content;private WebView web;private LocalBridge bridge;private Pairing pair;private ValueCallback<Uri[]> chooser;private PermissionRequest camera;private static final int PICK=7201,CAMERA=7202;
 private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);getWindow().setStatusBarColor(Color.rgb(20,66,119));getWindow().setNavigationBarColor(Color.rgb(20,66,119));WebView.setWebContentsDebuggingEnabled(false);
  root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(Color.rgb(242,246,251));setContentView(root);
  bar=new LinearLayout(this);bar.setGravity(Gravity.CENTER_VERTICAL);bar.setBackgroundColor(Color.rgb(20,66,119));bar.setPadding(dp(16),dp(10),dp(12),dp(10));root.addView(bar,new LinearLayout.LayoutParams(-1,-2));
  TextView title=new TextView(this);title.setText("Patente Studio");title.setTextColor(Color.WHITE);title.setTextSize(20);title.setTypeface(null,1);bar.addView(title,new LinearLayout.LayoutParams(0,-2,1));
  Button change=new Button(this);change.setText("Postazione");change.setAllCaps(false);bar.addView(change);change.setOnClickListener(v->confirmPair());
  content=new FrameLayout(this);root.addView(content,new LinearLayout.LayoutParams(-1,0,1));
  try{String stored=getPreferences(MODE_PRIVATE).getString("pair","");if(!stored.isEmpty())connect(Pairing.parse(stored));else showPair("");}catch(Exception e){showPair("Associa nuovamente il tablet.");}
 }
 private void confirmPair(){if(web==null){scan();return;}new AlertDialog.Builder(this).setTitle("Cambia postazione").setMessage("Termina o salva la pratica prima di cambiare PC.").setNegativeButton("Annulla",null).setPositiveButton("Collega altro PC",(d,w)->scan()).show();}
 private void showPair(String message){stopWeb();content.removeAllViews();LinearLayout p=new LinearLayout(this);p.setOrientation(LinearLayout.VERTICAL);p.setGravity(Gravity.CENTER);p.setPadding(dp(28),dp(28),dp(28),dp(28));content.addView(p,new FrameLayout.LayoutParams(-1,-1));
  TextView h=new TextView(this);h.setText("Collega la tua postazione");h.setGravity(Gravity.CENTER);h.setTextSize(28);h.setTextColor(0xff173b60);h.setTypeface(null,1);p.addView(h);
  TextView desc=new TextView(this);desc.setText("Apri Dispositivi su Patente Studio del PC e inquadra il QR. Tablet e PC devono essere sulla stessa rete Wi-Fi.");desc.setTextSize(16);desc.setGravity(Gravity.CENTER);desc.setPadding(0,dp(16),0,dp(24));p.addView(desc);
  Button b=new Button(this);b.setText("Scansiona QR");b.setAllCaps(false);p.addView(b,new LinearLayout.LayoutParams(-1,dp(55)));b.setOnClickListener(v->scan());
  if(!message.isEmpty()){TextView err=new TextView(this);err.setText(message);err.setTextColor(0xffa52a25);err.setGravity(Gravity.CENTER);err.setPadding(0,dp(18),0,0);p.addView(err);}
  if(pair!=null){Button retry=new Button(this);retry.setText("Riprova collegamento");retry.setAllCaps(false);p.addView(retry);retry.setOnClickListener(v->connect(pair));}
 }
 private void scan(){IntentIntegrator i=new IntentIntegrator(this);i.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE);i.setPrompt("Inquadra il QR di Patente Studio sul PC");i.setBeepEnabled(false);i.setOrientationLocked(false);i.initiateScan();}
 private void stopWeb(){if(camera!=null){camera.deny();camera=null;}if(web!=null){web.stopLoading();web.destroy();web=null;}if(bridge!=null){bridge.stop();bridge=null;}}
 private void connect(Pairing p){stopWeb();pair=p;content.removeAllViews();
  try{bridge=new LocalBridge(p);bridge.start(15000,true);String base=bridge.origin();web=new WebView(this);content.addView(web,new FrameLayout.LayoutParams(-1,-1));WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(true);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);s.setMediaPlaybackRequiresUserGesture(false);s.setCacheMode(WebSettings.LOAD_DEFAULT);s.setSupportMultipleWindows(false);
   web.setWebViewClient(new WebViewClient(){
    @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !r.getUrl().toString().startsWith(base+"/");}
    @Override public void onReceivedError(WebView v,WebResourceRequest r,WebResourceError e){if(r.isForMainFrame())v.post(()->{if(web==v)showPair("PC non raggiungibile. Verifica Wi-Fi e che Patente Studio sia aperto.");});}
    @Override public void onReceivedHttpError(WebView v,WebResourceRequest r,WebResourceResponse e){if(r.isForMainFrame())v.post(()->{if(web==v)showPair("PC non raggiungibile o certificato cambiato. Riprova o scansiona il nuovo QR.");});}
   });
   web.setWebChromeClient(new WebChromeClient(){
    @Override public void onPermissionRequest(PermissionRequest r){runOnUiThread(()->{if(!r.getOrigin().toString().equals(base)||!java.util.Arrays.asList(r.getResources()).contains(PermissionRequest.RESOURCE_VIDEO_CAPTURE)){r.deny();return;}if(checkSelfPermission(Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)r.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});else{camera=r;requestPermissions(new String[]{Manifest.permission.CAMERA},CAMERA);}});}
    @Override public void onPermissionRequestCanceled(PermissionRequest r){if(camera==r)camera=null;}
    @Override public boolean onShowFileChooser(WebView w,ValueCallback<Uri[]> cb,FileChooserParams params){if(chooser!=null)chooser.onReceiveValue(null);chooser=cb;Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);intent.setType("image/*");intent.addCategory(Intent.CATEGORY_OPENABLE);try{startActivityForResult(intent,PICK);}catch(Exception e){chooser.onReceiveValue(null);chooser=null;}return true;}
   });
   getPreferences(MODE_PRIVATE).edit().putString("pair",p.encoded()).apply();web.loadUrl(base+"/#pair="+p.token);
  }catch(Exception e){showPair("Impossibile avviare il collegamento locale.");}
 }
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==PICK){if(chooser!=null){chooser.onReceiveValue(result==RESULT_OK&&data!=null&&data.getData()!=null?new Uri[]{data.getData()}:null);chooser=null;}return;}IntentResult qr=IntentIntegrator.parseActivityResult(request,result,data);if(qr!=null&&qr.getContents()!=null){try{connect(Pairing.parse(qr.getContents()));}catch(Exception e){new AlertDialog.Builder(this).setTitle("QR non compatibile").setMessage(e.getMessage()).setPositiveButton("OK",null).show();}}}
 @Override public void onRequestPermissionsResult(int r,String[] p,int[] g){super.onRequestPermissionsResult(r,p,g);if(r==CAMERA&&camera!=null){if(g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)camera.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});else camera.deny();camera=null;}}
 @Override protected void onPause(){super.onPause();if(web!=null)web.onPause();}
 @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
 @Override protected void onDestroy(){stopWeb();super.onDestroy();}
}