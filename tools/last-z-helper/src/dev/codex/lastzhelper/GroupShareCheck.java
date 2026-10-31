package dev.codex.lastzhelper;
import java.io.*;import java.nio.channels.*;import org.json.*;
/** Explicitly live, one-truck group test. Requires the already-open confirmation UUID. */
public final class GroupShareCheck {
 public static void main(String[] args){try(DeviceInput.Scope scope=new DeviceInput.Scope()){
  if((args.length!=2&&args.length!=3)||!args[1].matches("[0-9]{10,24}")||(args.length==3&&!args[2].equals("--verify-only")))throw new IOException("Expected diagnostic directory, truck UUID and optional --verify-only");
  File dir=new File(args[0]),lockDir=new File("/data/local/tmp/codex-lastz-helper");lockDir.mkdirs();
  try(RandomAccessFile file=new RandomAccessFile(new File(lockDir,"control.lock"),"rw");FileChannel channel=file.getChannel();FileLock lock=channel.tryLock()){
   if(lock==null)throw new IOException("Controller already running");try(DisplaySession display=new DisplaySession()){
    AutomationController c=new AutomationController(new File("/data/user/0/dev.codex.lastzhelper/files"),new File(dir,"injector"),new File(dir,"input-agent.js"),new File(dir,"stop-request"),false,0);c.mode="group-test";c.input.foreground();
    GroupTruckSender sender=new GroupTruckSender(c);String id=args[1];
    if(args.length==3){JSONObject record=c.ledger.data.getJSONObject(GroupTruckSender.key(id));if(!StateProbe.pinnedUid.equals(record.getString("senderUid"))||!GroupTruckSender.ROOM.equals(record.getString("roomId")))throw new IOException("Recorded group attempt identity mismatch");long seq=sender.receipt(0,id);if(seq<1)throw new IOException("No matching group receipt; no input sent");c.ledger.verified(GroupTruckSender.key(id),seq);System.out.println(new JSONObject().put("ok",true).put("verifiedSequence",seq).put("sentNow",0).put("truckId",id));return;}
    if(c.ledger.contains(GroupTruckSender.key(id)))throw new IOException("Group attempt already recorded; no retry");c.truckMode="truck-dm";JSONObject target;
    try(GameMemory m=new GameMemory(c.cache)){long param=m.path("UIManagerInstance/windows/UIPositionShareConfirm/View/chat_data/param");int[] cargo=TruckCargo.payload(GameMemory.string(param,"rewardStr"));target=new JSONObject().put("id",id).put("quality",GameMemory.number(param,"quality")).put("power",GameMemory.number(param,"power")).put("orangeFragmentSlots",cargo[0]).put("moduleBoxIcons",cargo[1]);}
    sender.confirmation(target);long baseline=sender.receipt(0,null);
    c.ledger.pending(GroupTruckSender.key(id),new JSONObject(target.toString()).put("kind","group-truck-test").put("roomId",GroupTruckSender.ROOM).put("senderUid",StateProbe.pinnedUid).put("note",""));sender.commit(target,baseline);System.out.println(new JSONObject().put("ok",true).put("shared",c.sent).put("roomId",GroupTruckSender.ROOM).put("truckId",id).put("attacked",0));
   }
  }
 }catch(Throwable e){e.printStackTrace();System.exit(1);}}
}
