package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Bounded live validation on the already-active Gaarix character: at most one attack. */
public final class AttackCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length<2||args.length>3)throw new IOException("Expected live directory, diagnostic assets and optional refresh limit");int refreshes=args.length==3?Integer.parseInt(args[2]):30;if(refreshes<0||refreshes>200)throw new IOException("Attack validation permits at most 200 refreshes");File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Open Gaarix before live attack validation; no account selected or switched");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);c.truckMode="truck-attack";c.sendLimit=1;c.input.foreground();c.truckRun(refreshes);System.out.println(new JSONObject().put("ok",true).put("scanned",c.scanned).put("attacked",c.attacked).put("shared",c.sent));
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
