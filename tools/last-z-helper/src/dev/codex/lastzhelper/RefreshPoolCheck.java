package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.*;import org.json.*;
/** Bounded bot-only UUID sample. Refreshes lists without selecting or sharing trucks. */
public final class RefreshPoolCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=4)throw new IOException("Expected live directory, assets, bot UID and refresh count");int limit=Integer.parseInt(args[3]);if(limit<1||limit>300)throw new IOException("Sample bound 1..300");
  File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller already active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!args[2].equals(StateProbe.pinnedUid)||TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Expected active bot account required");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,true,0);c.mode="refresh-pool-sample";c.truckMode="truck-dm";c.input.foreground();c.ensureTrucks();int observations=0;
   try(TruckRefreshLog log=new TruckRefreshLog(dir,c.mode,c.attackPowerLimit)){
    System.out.println(new JSONObject().put("event","refresh-log").put("path",log.file.getPath()).put("accountUid",StateProbe.pinnedUid));System.out.flush();
    for(int refresh=0;refresh<=limit;refresh++){
     c.input.check();JSONObject snapshot=c.truckSnapshot();JSONArray trucks=snapshot.getJSONArray("loadedTrucks");log.record(refresh,trucks,c.rendered());observations+=trucks.length();
     if(refresh%25==0||refresh==limit){System.out.println(new JSONObject().put("event","sample-progress").put("refreshes",refresh).put("observations",observations));System.out.flush();}
     if(refresh==limit)break;Map<String,String> old=TruckProbe.identities(TruckProbe.readList(c.cache));c.refreshTrucks();c.waitRefreshed(old);
    }
   }
   System.out.println(new JSONObject().put("ok",true).put("refreshes",limit).put("observations",observations).put("shared",0).put("attacked",0));
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
