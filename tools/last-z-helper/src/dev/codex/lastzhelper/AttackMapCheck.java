package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Explicit continuation of a diagnosed pre-Plunder lookup failure; never an automatic retry. */
public final class AttackMapCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=3||!args[2].matches("[0-9]{10,24}"))throw new IOException("Expected live directory, diagnostic assets, verified unstarted truck UUID");File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Active Gaarix required");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);c.truckMode="truck-attack";c.mode="attack-map-check";c.input.foreground();JSONObject truck=c.attacks.data.getJSONObject("attack:"+args[2]);
   if(!args[2].equals(truck.getString("id")))throw new IOException("Recorded truck UUID mismatch");try{c.attackFromMap(truck);}catch(AutomationController.TruckChanged changed){c.skipChangedTruck(truck,changed.getMessage());}System.out.println(new JSONObject().put("ok",true).put("attacked",c.attacked).put("shared",c.sent).put("truckId",args[2]));
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
