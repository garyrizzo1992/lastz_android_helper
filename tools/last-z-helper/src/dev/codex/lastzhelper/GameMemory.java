package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Validated, read-only Lua access. A controller owns this resource serially. */
final class GameMemory implements AutoCloseable {
 final JSONObject state;final long globals;
 GameMemory(String cache)throws Exception {
  state=StateProbe.snapshot(cache);long manager=StateProbe.pinnedManager;
  StateProbe.mem=new RandomAccessFile("/proc/"+state.getInt("pid")+"/mem","r");
  long L=StateProbe.ptr(StateProbe.ptr(manager+32)+16);
  globals=StateProbe.ptr(StateProbe.ptr(StateProbe.ptr(StateProbe.ptr(L+24)+64)+16)+16);
 }
 static long f(long t,String key)throws Exception{
  if(key.startsWith("#")){for(TruckDiscoveryProbe.Value v:TruckDiscoveryProbe.rows(t))if(v.key.equals(key))return v.raw;throw new IOException("Missing index "+key);}
  return StateProbe.ptr(StateProbe.findField(t,key));
 }
 static long optional(long t,String key){try{return f(t,key);}catch(Exception e){return 0;}}
 static long number(long t,String key)throws Exception{return StateProbe.number(t,key);}
 static double decimal(long t,String key)throws Exception{long a=StateProbe.findField(t,key),v=StateProbe.ptr(a);return StateProbe.u8(a+8)==19?Double.longBitsToDouble(v):v;}
 static String string(long t,String key)throws Exception{return StateProbe.luaString(f(t,key));}
 static String attachment(long t)throws Exception{long p=f(t,"attachmentId"),length=StateProbe.u8(p+8)%64==4?StateProbe.u8(p+11):StateProbe.ptr(p+16);if(length<1||length>16384)throw new IOException("Chat attachment length bound");return new String(StateProbe.bytes(p+24,(int)length),java.nio.charset.StandardCharsets.UTF_8);}
 static boolean bool(long t,String key){try{return StateProbe.u8(StateProbe.findField(t,key)+8)==17;}catch(Exception e){return false;}}
 static List<TruckDiscoveryProbe.Value> rows(long t)throws Exception{
  List<TruckDiscoveryProbe.Value> out=new ArrayList<>(TruckDiscoveryProbe.rows(t));long size=StateProbe.ptr(t+8)>>>32,array=StateProbe.ptr(t+16);
  if(size>8192)throw new IOException("Lua array exceeds supported read bound");
  for(int i=128;i<size&&array!=0;i++){long a=array+i*16L;int tag=StateProbe.u8(a+8);if((tag&15)!=0)out.add(new TruckDiscoveryProbe.Value("#"+(i+1),tag,a,StateProbe.ptr(a)));}
  return out;
 }
 long path(String path)throws Exception{long t=globals;for(String k:path.split("/"))t=f(t,k);return t;}
 boolean open(String name){try{return number(path("UIManagerInstance/windows/"+name),"State")==2;}catch(Exception e){return false;}}
 public void close()throws Exception{if(!state.getString("processStart").equals(StateProbe.start(String.valueOf(state.getInt("pid")))))throw new IOException("Game process changed");if(StateProbe.mem!=null){StateProbe.mem.close();StateProbe.mem=null;}}
}
