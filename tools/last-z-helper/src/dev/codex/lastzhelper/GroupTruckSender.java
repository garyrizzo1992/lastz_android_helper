package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Native truck tile sharing to the user-created trucks group. */
final class GroupTruckSender {
 static final String ROOM="custom_vip_2028198887000064_1793214114",NAME="trucks";
 static final String SCROLL="UIManagerInstance/windows/UIPositionShare/View/ScrollView";
 final AutomationController c;GroupTruckSender(AutomationController c){this.c=c;}
 static String key(String id){return "group-truck:"+ROOM+":"+id;}
 void room()throws Exception{try(GameMemory m=new GameMemory(c.cache)){
  long r=m.path("ChatManager2/Instance/Room/roomDatas/"+ROOM);
  if(!ROOM.equals(GameMemory.string(r,"roomId"))||!NAME.equals(GameMemory.string(r,"name"))||!TruckPolicy.MAIN_UID.equals(GameMemory.string(r,"owner")))throw new IOException("Trucks group identity changed; no share sent");
 }}
 int row()throws Exception{room();try(GameMemory m=new GameMemory(c.cache)){
  if(!m.open("UIPositionShare"))throw new IOException("Truck share menu missing");int found=0;
  for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("UIManagerInstance/windows/UIPositionShare/View/list")))if((v.tag&15)==5&&NAME.equals(GameMemory.string(v.raw,"name"))){if(found!=0||!ROOM.equals(GameMemory.string(v.raw,"roomId")))throw new IOException("Ambiguous trucks group in share list");found=Integer.parseInt(v.key.substring(1));}
  if(found==0)throw new IOException("Trucks group missing from share list");return found;
 }}
 JSONObject rowAction(String action,int index)throws Exception{return new JSONObject().put("action",action).put("path",SCROLL).put("child","Viewport/Content/"+index+"/ImgBg/ImageShare").put("expectedLabel",NAME);}
 void reveal()throws Exception{
  for(int attempt=0;attempt<16;attempt++){int index=row();boolean above=false;try{c.input.action(rowAction("ui-bounds",index));return;}catch(IOException e){if(!e.getMessage().contains("outside visible")&&!e.getMessage().contains("Unity child missing"))throw e;above=e.getMessage().contains("above");}
   c.input.scrollControl(SCROLL,above?"down":"up");
  }throw new IOException("Trucks group did not become visible after scrolling");
 }
 void confirmation(JSONObject truck)throws Exception{String id=truck.getString("id");room();try(GameMemory m=new GameMemory(c.cache)){
  if(!m.open("UIPositionShareConfirm"))throw new IOException("Trucks group share confirmation missing");long data=m.path("UIManagerInstance/windows/UIPositionShareConfirm/View/chat_data"),param=GameMemory.f(data,"param");
  if(!ROOM.equals(GameMemory.string(data,"roomId"))||GameMemory.number(data,"post")!=604||!id.equals(Long.toString(GameMemory.number(param,"trainUuid")))||!GameMemory.string(param,"msg").isEmpty())throw new IOException("Group share confirmation truck/destination/note changed");c.validateTruckShareParam(truck,param);
 }JSONObject draft=c.input.action(new JSONObject().put("action","ui-bounds").put("path","UIManagerInstance/windows/UIPositionShareConfirm/View/input_field").put("readText",true));if(!draft.getString("inputText").isEmpty())throw new IOException("Group share note must be empty");}
 long receipt(long after,String id)throws Exception{return receipt(after,id,604);}
 long receipt(long after,String id,int post)throws Exception{if(post!=604&&post!=630)throw new IOException("Unsupported group tile");room();try(GameMemory m=new GameMemory(c.cache)){
  long best=0;for(TruckDiscoveryProbe.Value v:GameMemory.rows(m.path("ChatManager2/Instance/Room/roomDatas/"+ROOM+"/msgs")))if((v.tag&15)==5){long seq=GameMemory.number(v.raw,"seqId");if(id==null){best=Math.max(best,seq);continue;}
   if(seq>after&&GameMemory.number(v.raw,"post")==post&&GameMemory.number(v.raw,"sendState")==0&&StateProbe.pinnedUid.equals(GameMemory.string(v.raw,"senderUid"))&&ROOM.equals(GameMemory.string(v.raw,"roomId"))){
    String actual=ChatTileIdentity.read(v.raw,post);
    if(id.equals(actual))best=Math.max(best,seq);
   }
  }return best;
 }}
 void commit(JSONObject truck,long baseline)throws Exception{String id=truck.getString("id");
  if(c.dryRun)throw new IOException("Preview cannot commit a group share");confirmation(truck);c.input.tapControl("UIManagerInstance/windows/UIPositionShareConfirm/View/btn_yes");long until=System.currentTimeMillis()+15000;
  while(System.currentTimeMillis()<until){long seq=receipt(baseline,id);if(seq>baseline){c.ledger.verified(key(id),seq);c.sent++;c.event("Truck tile shared to trucks group");return;}c.input.pause(250);}
  throw new IOException("Trucks group outcome uncertain; attempt saved and will not be retried");
 }
 void send(JSONObject truck)throws Exception{
  String id=truck.getString("id"),key=key(id);if(c.ledger.contains(key)||c.drySeen.contains(key))return;
  if(!c.classify(truck).equals("PRIVATE_SHARE_ELIGIBLE"))throw new IOException("Truck does not qualify for group share");c.validateShare(truck,true);reveal();
  if(c.dryRun){c.drySeen.add(key);c.planned++;c.event("Preview: qualifying truck and trucks group verified; no share sent");c.closeShare();return;}
  c.validateShare(truck,true);long baseline=receipt(0,null);int index=row();
  c.ledger.pending(key,new JSONObject(truck.toString()).put("kind","group-truck").put("roomId",ROOM).put("senderUid",StateProbe.pinnedUid).put("note",""));
  c.input.action(rowAction("ui-tap",index));c.input.pause(450);c.waitWindow("UIPositionShareConfirm",5000);c.validateShare(truck,true);commit(truck,baseline);if(c.open("UIPositionShare"))c.closeShare();c.ensureTrucks();
 }
}
