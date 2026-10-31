package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import java.util.*;import org.json.*;
/** Refresh-only benchmark. Never opens a target, sends a message or starts a battle. */
public final class RefreshBench {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length<2||args.length>4)throw new IOException("Expected live directory, assets, optional cycle count and label");int cycles=args.length>2?Integer.parseInt(args[2]):5;if(cycles<1||cycles>20)throw new IOException("Benchmark limit 1..20 cycles");String label=args.length>3?args[3]:"baseline";
  File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,true,0);c.mode="refresh-benchmark";c.truckMode="truck-attack";c.input.foreground();c.ensureTrucks();
   Perf.enabled=true;JSONArray reports=new JSONArray();
   for(int cycle=0;cycle<cycles;cycle++){
    Perf.reset();long begin=System.nanoTime();c.input.check();JSONObject snapshot=c.truckSnapshot();c.rendered();long analyzed=System.nanoTime();
    c.input.check();c.ensureTrucks();Map<String,String> old=TruckProbe.identities(TruckProbe.readList(c.cache));long prepared=System.nanoTime();c.refreshTrucks();long tapped=System.nanoTime();c.waitRefreshed(old);
    long end=System.nanoTime();JSONObject report=Perf.report().put("label",label).put("cycle",cycle+1).put("trucks",snapshot.getInt("loadedTruckCount")).put("analyzeMs",(analyzed-begin)/1e6).put("prepareMs",(prepared-analyzed)/1e6).put("tapMs",(tapped-prepared)/1e6).put("waitForChangeMs",(end-tapped)/1e6).put("cycleMs",(end-begin)/1e6);reports.put(report);System.out.println(report);System.out.flush();
   }
   Perf.enabled=false;System.out.println(new JSONObject().put("ok",true).put("label",label).put("cycles",reports).put("shared",0).put("attacked",0));
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
