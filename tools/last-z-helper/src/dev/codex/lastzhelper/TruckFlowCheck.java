package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Explicit live diagnostic: share-one sends at most one qualifying truck tile. */
public final class TruckFlowCheck {
 public static void main(String[] a)throws Exception{
  try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  File dir=new File(a[1]),stop=new File(dir,"stop-request");
  try(RandomAccessFile f=new RandomAccessFile("/data/local/tmp/codex-lastz-helper/control.lock","rw");FileChannel channel=f.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Controller already active");if(!a[0].equals("share-one")&&!a[0].equals("attack-one")&&!a[0].equals("return-result"))throw new IOException("Expected explicit live diagnostic");stop.delete();
   AutomationController c=new AutomationController(dir,new File(dir,"injector-17.24.3"),new File(dir,"input-agent-v06.js"),stop,false,0,a[0].equals("return-result"));c.mode="share-one-test";c.skipTruckState=Integer.parseInt(a[2]);c.input.foreground();if(a[0].equals("return-result")){c.returnFromBattle();System.out.println("Battle return verified");return;}
   c.truckMode=a[0].equals("attack-one")?"truck-attack":"truck-world";if(a[0].equals("attack-one"))c.attackPowerLimit=1000000L*TruckRules.parsePowerLimit(a[3]);c.ensureTrucks();
   for(int refresh=0;refresh<=20;refresh++){
    if(!c.open("UILWTrainScene")||StateProbe.snapshot(c.cache).getInt("modalWindowCount")!=1)throw new IOException("Unexpected truck dialog in diagnostic");JSONObject snapshot=c.truckSnapshot();JSONArray candidates=snapshot.getJSONArray("candidates");java.util.Set<String> visible=c.rendered();System.out.println("Diagnostic list "+refresh);System.out.flush();
    if(a[0].equals("attack-one")){for(int i=0;i<candidates.length();i++){JSONObject t=candidates.getJSONObject(i);if(!t.getString("decision").equals("ALERT_TARGET")||!visible.contains(t.getString("id"))||c.attacks.contains("attack:"+t.getString("id")))continue;if(!c.openTruck(t))continue;c.attackTruck(t);System.out.println(new JSONObject().put("ok",true).put("attacked",c.attacked).put("truck",t));return;}if(refresh==20)break;c.refreshTrucks();c.input.pause(1000);continue;}
    for(int i=0;i<candidates.length();i++){JSONObject t=candidates.getJSONObject(i);String id=t.getString("id");if(!t.getString("decision").equals("WORLD_SHARE_ELIGIBLE")||!TruckRules.shareAllowed(t.getLong("serverId"),c.skipTruckState)||!visible.contains(id)||c.ledger.contains("truck:"+id))continue;if(!c.openTruck(t))continue;c.truckShare();long started=System.currentTimeMillis();if(c.share(t,true)){System.out.println(new JSONObject().put("ok",true).put("truck",t).put("totalShareAndSummaryMs",System.currentTimeMillis()-started));return;}}
    if(refresh==20)break;c.refreshTrucks();c.input.pause(1000);
   }throw new IOException("No share candidate in bounded diagnostic");
  }
  }
 }
}
