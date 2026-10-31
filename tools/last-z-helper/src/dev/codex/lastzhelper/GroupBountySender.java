package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Bounty tiles to the pinned Gaarix-owned trucks room, with no World side-post. */
final class GroupBountySender {
 final AutomationController c;final GroupTruckSender destination;
 GroupBountySender(AutomationController c){this.c=c;destination=new GroupTruckSender(c);}
 static String key(String id){return BountyRoute.key(true,GroupTruckSender.ROOM,id);}
 void confirmation(JSONObject bounty)throws Exception{
  destination.room();c.validateShare(bounty,false);
  try(GameMemory m=new GameMemory(c.cache)){
   if(!m.open("UIPositionShareConfirm"))throw new IOException("Bounty group confirmation missing");
   long data=m.path("UIManagerInstance/windows/UIPositionShareConfirm/View/chat_data"),param=GameMemory.f(data,"param");
   if(!GroupTruckSender.ROOM.equals(GameMemory.string(data,"roomId"))||GameMemory.number(data,"post")!=630||!bounty.getString("uuid").equals(GameMemory.string(param,"dispatchTaskUuid"))||GameMemory.number(param,"sid")!=bounty.getInt("server")||GameMemory.number(param,"x")!=bounty.getInt("x")||GameMemory.number(param,"y")!=bounty.getInt("y"))throw new IOException("Bounty group confirmation identity/destination changed");
   long note=GameMemory.optional(param,"msg");if(note!=0&&!StateProbe.luaString(note).isEmpty())throw new IOException("Bounty share note must be empty");
  }
  JSONObject draft=c.input.action(new JSONObject().put("action","ui-bounds").put("path","UIManagerInstance/windows/UIPositionShareConfirm/View/input_field").put("readText",true));if(!draft.getString("inputText").isEmpty())throw new IOException("Bounty group note is not empty");
 }
 boolean send(JSONObject bounty)throws Exception{
  String id=bounty.getString("uuid"),key=key(id);if(c.ledger.contains(key)||c.drySeen.contains(key))return false;
  c.validateShare(bounty,false);destination.reveal();
  if(c.dryRun){c.drySeen.add(key);c.planned++;c.event("Preview: qualifying bounty and trucks group verified; no share sent");c.closeShare();return false;}
  c.validateShare(bounty,false);long baseline=destination.receipt(0,null,630);int row=destination.row();
  c.ledger.pending(key,new JSONObject(bounty.toString()).put("kind","group-bounty").put("roomId",GroupTruckSender.ROOM).put("senderUid",StateProbe.pinnedUid).put("note",""));
  c.input.action(destination.rowAction("ui-tap",row));c.input.pause(450);c.waitWindow("UIPositionShareConfirm",5000);confirmation(bounty);
  c.input.tapControl("UIManagerInstance/windows/UIPositionShareConfirm/View/btn_yes");long until=System.currentTimeMillis()+15000;
  while(System.currentTimeMillis()<until){long seq=destination.receipt(baseline,id,630);if(seq>baseline){c.ledger.verified(key,seq);c.sent++;c.event("Bounty tile shared to trucks group");if(c.open("UIPositionShare"))c.closeShare();return true;}c.input.pause(250);}
  throw new IOException("Bounty group outcome uncertain; saved attempt will not be retried");
 }
}
