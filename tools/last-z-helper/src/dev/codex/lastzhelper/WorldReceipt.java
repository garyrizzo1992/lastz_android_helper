package dev.codex.lastzhelper;
import org.json.*;
final class WorldReceipt {
 final String cache;WorldReceipt(String cache){this.cache=cache;}
 long baseline()throws Exception{return read(0,0);}
 long textReceipt(long after,String expected)throws Exception{
  try(GameMemory m=new GameMemory(cache)){long manager=m.path("ChatManager2/Instance"),rooms=GameMemory.f(manager,"Room");String uid=GameMemory.string(manager,"cur_gameuid"),room=GameMemory.string(rooms,"countryRoomId");if(!room.startsWith("country_"))throw new java.io.IOException("World chat unavailable");long messages=GameMemory.f(GameMemory.f(GameMemory.f(rooms,"roomDatas"),room),"msgs");for(TruckDiscoveryProbe.Value v:GameMemory.rows(messages))if((v.tag&15)==5&&GameMemory.number(v.raw,"seqId")>after&&GameMemory.number(v.raw,"post")==0&&GameMemory.number(v.raw,"sendState")==0&&uid.equals(GameMemory.string(v.raw,"senderUid"))&&expected.equals(GameMemory.string(v.raw,"msg")))return GameMemory.number(v.raw,"seqId");return 0;}
 }
 long read(long after,int post)throws Exception{
  return read(after,post,null);
 }
 long read(long after,int post,String identity)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   long manager=m.path("ChatManager2/Instance"),rooms=GameMemory.f(manager,"Room");String uid=GameMemory.string(manager,"cur_gameuid"),room=GameMemory.string(rooms,"countryRoomId");
   if(!room.startsWith("country_")||!uid.matches("[0-9]{8,24}"))throw new java.io.IOException("World chat identity unavailable");
   long messages=GameMemory.f(GameMemory.f(GameMemory.f(rooms,"roomDatas"),room),"msgs"),best=0;
   for(TruckDiscoveryProbe.Value v:GameMemory.rows(messages))if((v.tag&15)==5){long sequence=GameMemory.number(v.raw,"seqId");if(post==0)best=Math.max(best,sequence);else if(sequence>after&&GameMemory.number(v.raw,"post")==post&&uid.equals(GameMemory.string(v.raw,"senderUid"))&&GameMemory.number(v.raw,"sendState")==0&&room.equals(GameMemory.string(v.raw,"roomId"))){if(identity!=null&&!identity.equals(ChatTileIdentity.read(v.raw,post)))continue;best=Math.max(best,sequence);}}
   return best;
  }
 }
}
