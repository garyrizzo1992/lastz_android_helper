package dev.codex.lastzhelper;
import java.net.URLDecoder;import java.util.*;import java.util.regex.*;
public final class LinkRules {
 public static boolean coordinates(String link,String name,String abbr,long server,long x,long y){
  if(link==null||link.length()>1024||server<1||x<0||y<0)return false;
  String suffix=" [#:"+server+" X:"+x+" Y:"+y+"]";
  return link.equals(name+suffix)||link.equals("["+abbr+"]"+name+suffix);
 }
 public static boolean containsTruck(String link,String id){
  if(link==null||link.length()>8192||!id.matches("[0-9]{10,24}"))return false;
  String decoded=link;try{decoded=URLDecoder.decode(link,"UTF-8");}catch(Exception ignored){}
  for(String candidate:new String[]{link,decoded}){
   if(candidate.contains(id))return true;
   Matcher m=Pattern.compile("[A-Za-z0-9_+/-]{16,4096}={0,2}").matcher(candidate);
   while(m.find())for(Base64.Decoder decoder:new Base64.Decoder[]{Base64.getDecoder(),Base64.getUrlDecoder()})try{if(new String(decoder.decode(m.group()),"UTF-8").contains(id))return true;}catch(Exception ignored){}
  }
  return false;
 }
}
