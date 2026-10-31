package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.*;import org.json.*;
/** Explicit one-battle defeat recovery diagnostic; never changes saved attack rules. */
public final class DefeatCheck {
 public static void main(String[] args){try(DeviceInput.Scope scope=new DeviceInput.Scope()){
  if(args.length!=2)throw new IOException("Expected live directory and assets");File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Active Gaarix required");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);c.truckMode="truck-attack";c.mode="one-defeat-check";c.twoFragmentTest=true;c.diagnosticMinimumSlots=1;c.diagnosticDefeatTest=true;c.attackPowerLimit=Long.MAX_VALUE;c.input.foreground();c.ensureTrucks();
   for(int refresh=0;refresh<=30;refresh++){
    JSONArray trucks=c.truckSnapshot().getJSONArray("candidates");Set<String> rendered=c.rendered();
    for(int i=0;i<trucks.length();i++){JSONObject t=trucks.getJSONObject(i);String id=t.getString("id");if(t.getLong("power")<500000000L||!c.classify(t).equals("ALERT_TARGET")||!rendered.contains(id)||c.attacks.contains("attack:"+id))continue;
     if(!c.openTruck(t))continue;System.out.println(new JSONObject().put("event","defeat-target").put("truck",t));System.out.flush();c.attackTruck(t);if(c.attacked==0){c.ensureTrucks();continue;}
     JSONObject record=c.attacks.data.getJSONObject("attack:"+id);System.out.println(new JSONObject().put("ok",true).put("attacked",c.attacked).put("record",record).put("returnedToTrucks",c.open("UILWTrainScene")));return;
    }
    if(refresh==30)break;Map<String,String> old=TruckProbe.identities(TruckProbe.readList(c.cache));c.refreshTrucks();try{c.waitRefreshed(old);}catch(IOException unchanged){c.input.pause(1000);c.refreshTrucks();c.waitRefreshed(old);}
   }
   throw new IOException("No high-power diagnostic candidate in bounded sample");
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
