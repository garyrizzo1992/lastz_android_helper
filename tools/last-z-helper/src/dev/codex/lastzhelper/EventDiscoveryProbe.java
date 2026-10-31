package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Bounded read-only event discovery; no injected session or gameplay actions. */
public final class EventDiscoveryProbe {
 static JSONArray describe(GameMemory m,String path,int depth)throws Exception{if(path.equals("EventGlobals")){JSONArray a=new JSONArray();for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.globals))if(v.key.matches("(?i).*(auto.*(join|rally)|(join|rally).*auto).*")){JSONObject row=v.json();if((v.tag&15)==5)row.put("fields",TruckDiscoveryProbe.describe(v.raw,1));a.put(row);}return a;}if(depth!=0)return TruckDiscoveryProbe.describe(m.path(path),depth);JSONArray a=new JSONArray();for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path(path))){if(a.length()>=2048)throw new IOException("Manager list bound");a.put(v.json());}return a;}
 public static void main(String[] args){try{
  if(args.length<2||args.length>3)throw new IOException("Expected cache, path and optional depth");String path=args[1];int depth=args.length==3?Integer.parseInt(args[2]):0;
  if(depth<0||depth>2||path.length()>300||!(path.equals("EventGlobals")||path.equals("DataCenter")||path.startsWith("DataCenter/")||path.equals("UIManagerInstance/windows")||path.startsWith("UIManagerInstance/windows/")))throw new IOException("Event inspection scope/bound");
  File locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Another controller is active");ControllerOwnership.check();RecoveryGuard.noInjector();try(GameMemory m=new GameMemory(args[0])){System.out.println(new JSONObject().put("state",m.state).put("path",path).put("readOnly",true).put("fields",describe(m,path,depth)).toString(2));}
  }
 }catch(Throwable e){try{System.out.println(new JSONObject().put("ok",false).put("error",e.toString()));}catch(Exception ignored){}System.exit(1);}}
}
