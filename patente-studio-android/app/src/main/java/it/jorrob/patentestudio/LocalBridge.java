package it.jorrob.patentestudio;
import fi.iki.elonen.NanoHTTPD;
import javax.net.ssl.*;
import java.net.*;
import java.io.*;
import java.security.*;
import java.security.cert.*;
import java.util.*;
final class LocalBridge extends NanoHTTPD {
 private final Pairing pair;
 private final SSLSocketFactory factory;
 private static final Set<String> GET_API=Set.of("/api/health","/api/session");
 private static final Set<String> POST_API=Set.of("/api/jobs","/api/analyze","/api/lan/claim","/api/lan/heartbeat");
 LocalBridge(Pairing p)throws Exception{
  super("127.0.0.1",0);pair=p;
  SSLContext c=SSLContext.getInstance("TLS");
  byte[] expected=new byte[32];for(int i=0;i<32;i++)expected[i]=(byte)Integer.parseInt(p.pin.substring(i*2,i*2+2),16);
  c.init(null,new TrustManager[]{new X509TrustManager(){
   public X509Certificate[] getAcceptedIssuers(){return new X509Certificate[0];}
   public void checkClientTrusted(X509Certificate[] certs,String a)throws CertificateException{throw new CertificateException("Client non valido");}
   public void checkServerTrusted(X509Certificate[] chain,String a)throws CertificateException{
    try{if(chain==null||chain.length==0)throw new CertificateException("Certificato mancante");chain[0].checkValidity();byte[] actual=MessageDigest.getInstance("SHA-256").digest(chain[0].getEncoded());if(!MessageDigest.isEqual(actual,expected))throw new CertificateException("Certificato della postazione cambiato");}
    catch(GeneralSecurityException e){throw new CertificateException(e);}
   }
  }},new SecureRandom());factory=c.getSocketFactory();
 }
 String origin(){return "http://127.0.0.1:"+getListeningPort();}
 private Response fail(Response.Status s,String msg){Response r=newFixedLengthResponse(s,"application/json; charset=utf-8","{\"error\":\""+msg+"\"}");r.addHeader("Cache-Control","no-store");return r;}
 private static boolean allowedStatic(String path){
  return path.equals("/")||path.matches("/[A-Za-z0-9_.-]+\\.(html|js|css|webmanifest|png)")||path.matches("/icons/[A-Za-z0-9_.-]+\\.png")||path.matches("/ai/[A-Za-z0-9_./-]+");
 }
 @Override public Response serve(IHTTPSession s){
  HttpsURLConnection c=null;
  try {
   String path=s.getUri(),method=s.getMethod().name();Map<String,String> h=s.getHeaders();
   if(!("127.0.0.1:"+getListeningPort()).equals(h.get("host"))||path.contains("..")||path.contains("\\")||s.getQueryParameterString()!=null)return fail(Response.Status.FORBIDDEN,"Richiesta non consentita");
   String origin=h.get("origin");if(origin!=null&&!origin.equals(origin()))return fail(Response.Status.FORBIDDEN,"Origine non consentita");
   if("cross-site".equals(h.get("sec-fetch-site")))return fail(Response.Status.FORBIDDEN,"Origine non consentita");
   boolean api=path.startsWith("/api/");
   if(!((method.equals("GET")&&(GET_API.contains(path)||(!api&&allowedStatic(path))))||(method.equals("POST")&&POST_API.contains(path))))return fail(Response.Status.FORBIDDEN,"Richiesta non consentita");
   if(api&&!path.equals("/api/health")&&!MessageDigest.isEqual(("Bearer "+pair.token).getBytes(java.nio.charset.StandardCharsets.UTF_8),Objects.toString(h.get("authorization"),"").getBytes(java.nio.charset.StandardCharsets.UTF_8)))return fail(Response.Status.UNAUTHORIZED,"Tablet non associato");
   c=(HttpsURLConnection)new URL(pair.remote()+path).openConnection(Proxy.NO_PROXY);
   c.setSSLSocketFactory(factory);c.setInstanceFollowRedirects(false);c.setConnectTimeout(10000);c.setReadTimeout(150000);c.setRequestMethod(method);c.setRequestProperty("Accept-Encoding","identity");
   if(api&&!path.equals("/api/health"))c.setRequestProperty("Authorization","Bearer "+pair.token);
   if(method.equals("POST")){
    long len=Long.parseLong(Objects.toString(h.get("content-length"),"-1"));if(len<0||len>14*1024*1024)return fail(Response.Status.BAD_REQUEST,"Dimensione non valida");
    if(!Objects.toString(h.get("content-type"),"").startsWith("application/json"))return fail(Response.Status.BAD_REQUEST,"Formato non valido");
    c.setRequestProperty("Content-Type","application/json");c.setRequestProperty("Origin",pair.remote());c.setDoOutput(true);c.setFixedLengthStreamingMode(len);
    try(OutputStream out=c.getOutputStream()){InputStream in=s.getInputStream();byte[] buf=new byte[16384];long left=len;while(left>0){int read=in.read(buf,0,(int)Math.min(buf.length,left));if(read<0)throw new IOException("Incomplete body");out.write(buf,0,read);left-=read;}}
   }
   int code=c.getResponseCode();if(code>=300&&code<400){c.disconnect();return fail(Response.Status.BAD_GATEWAY,"Risposta non valida");}
   InputStream raw=code>=400?c.getErrorStream():c.getInputStream();if(raw==null)raw=new ByteArrayInputStream(new byte[0]);final HttpsURLConnection conn=c;
   InputStream data=new FilterInputStream(raw){@Override public void close()throws IOException{try{super.close();}finally{conn.disconnect();}}};
   Response.IStatus status=new Response.IStatus(){public int getRequestStatus(){return code;}public String getDescription(){return code+" Remote";}};
   long len=c.getContentLengthLong();String mime=Objects.toString(c.getContentType(),"application/octet-stream");Response r=len>=0?newFixedLengthResponse(status,mime,data,len):newChunkedResponse(status,mime,data);
   for(String k:new String[]{"Content-Security-Policy","X-Content-Type-Options","Referrer-Policy","X-Frame-Options","Cross-Origin-Resource-Policy","Permissions-Policy","Cache-Control"}){String v=c.getHeaderField(k);if(v!=null)r.addHeader(k,v);}
   if(api)r.addHeader("Cache-Control","no-store");return r;
  }catch(Exception e){if(c!=null)c.disconnect();return fail(Response.Status.SERVICE_UNAVAILABLE,"PC non raggiungibile o certificato cambiato. Verifica Wi-Fi e associa nuovamente la postazione.");}
 }
}