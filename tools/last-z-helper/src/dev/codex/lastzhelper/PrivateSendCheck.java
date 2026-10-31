package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;
/** Explicit bounded live test: at most one qualifying trucks-group tile, no attacks. */
public final class PrivateSendCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length<3||args.length>4)throw new IOException("Expected live app directory, diagnostic assets directory, expected scanning UID, optional refresh limit");int refreshes=args.length==4?Integer.parseInt(args[3]):30;if(refreshes<0||refreshes>300)throw new IOException("Group validation permits at most 300 refreshes");
  File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller already active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());
   if(!args[2].equals(StateProbe.pinnedUid)||TruckPolicy.MAIN_UID.equals(StateProbe.pinnedUid))throw new IOException("Live test requires the expected scanning account already active");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);
   c.truckMode="truck-dm";c.sendLimit=1;c.logRefreshes=true;c.input.foreground();c.truckRun(refreshes);System.out.println("Group test finished: sent="+c.sent+", scanned="+c.scanned+", attacks="+c.attacked);
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
