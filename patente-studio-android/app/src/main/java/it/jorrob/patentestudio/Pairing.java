package it.jorrob.patentestudio;
import java.net.URI;
import java.util.*;
import java.util.regex.*;
final class Pairing {
 final String host, token, pin;
 Pairing(String h,String t,String p){host=h;token=t;pin=p;}
 String remote(){return "https://"+host+":18886";}
 String encoded(){return remote()+"/#pair="+token+"&pin="+pin;}
 static Pairing parse(String input) throws Exception {
  URI u=new URI(input.trim());
  String h=u.getHost();
  if(!"https".equals(u.getScheme())||u.getPort()!=18886||h==null||u.getUserInfo()!=null||u.getQuery()!=null||!"/".equals(u.getPath())||!localIP(h))throw new Exception("QR postazione non valido.");
  Matcher m=Pattern.compile("pair=([A-Za-z0-9_-]{43})&pin=([0-9a-f]{64})").matcher(Objects.toString(u.getRawFragment(),""));
  if(!m.matches())throw new Exception("Aggiorna Patente Studio sul PC alla versione 0.8.8 o successiva e scansiona il nuovo QR.");
  return new Pairing(h,m.group(1),m.group(2));
 }
 static boolean localIP(String h){
  String[] p=h.split("\\.",-1);if(p.length!=4)return false;
  int[] n=new int[4];try{for(int i=0;i<4;i++){if(!p[i].matches("0|[1-9][0-9]{0,2}"))return false;n[i]=Integer.parseInt(p[i]);if(n[i]>255)return false;}}catch(Exception e){return false;}
  return n[0]==10||(n[0]==172&&n[1]>=16&&n[1]<=31)||(n[0]==192&&n[1]==168);
 }
}