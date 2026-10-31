package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Bounded live bounty check: one state, at most one qualifying share, no checkpoint writes. */
public final class BountySendCheck {
 public static void main(String[] args){try(DeviceInput.Scope inputs=new DeviceInput.Scope()){
  if(args.length!=4&&args.length!=6)throw new IOException("Expected live directory, diagnostic assets, scanning UID, state");int state=Integer.parseInt(args[3]);if(state<17||state>64)throw new IOException("State must be in the authorized range 17..64");
  File dir=new File(args[0]),assets=new File(args[1]),locks=new File("/data/local/tmp/codex-lastz-helper");locks.mkdirs();
  try(RandomAccessFile f=new RandomAccessFile(new File(locks,"control.lock"),"rw");FileChannel ch=f.getChannel();FileLock lock=ch.tryLock()){
   if(lock==null)throw new IOException("Controller already active");StateProbe.pinForeground();StateProbe.snapshot(new File(dir,"probe-cache.txt").getPath());if(!args[2].equals(StateProbe.pinnedUid))throw new IOException("Expected scanning account is not active");
   File stop=new File(dir,"stop-request");stop.delete();AutomationController c=new AutomationController(dir,new File(assets,"injector"),new File(assets,"input-agent.js"),stop,false,0);c.mode="bounty-live-check";c.sendLimit=1;c.input.foreground();
   int x=args.length==6?Integer.parseInt(args[4]):500,y=args.length==6?Integer.parseInt(args[5]):500;if(x<0||x>9999||y<0||y>9999)throw new IOException("Map coordinate bound");if(!c.go(state,x,y))throw new IOException("State unavailable");if(x==500&&y==500)c.capital(state);c.zoom();c.scanBounties(state);
   String[] route=MapSweep.DIRECTIONS;
   for(String move:route){if(c.sent>=1)break;c.moveMap(move);c.scanBounties(state);}
   System.out.println(new JSONObject().put("ok",true).put("state",state).put("scanned",c.scanned).put("shared",c.sent).put("attacked",c.attacked));
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
