package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;
/** Bounded live validation: one eligible World truck tile, real dedup ledger. */
public final class WorldSendCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  File dir=new File(args[0]),assets=new File(args[1]);
  try(RandomAccessFile f=new RandomAccessFile("/data/local/tmp/codex-lastz-helper/control.lock","rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!args[2].equals(StateProbe.pinnedUid))throw new IOException("Scanning account changed");
   int refreshes=args.length>3?Integer.parseInt(args[3]):3;if(refreshes<0||refreshes>10)throw new IOException("Bounded test permits at most 10 refreshes");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);c.truckMode="truck-world";c.sendLimit=1;c.input.foreground();c.truckRun(refreshes);System.out.println("World test finished: sent="+c.sent+", scanned="+c.scanned+", attacks="+c.attacked);
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
