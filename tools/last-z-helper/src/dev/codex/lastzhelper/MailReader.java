package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Reads loaded headers only. It does not equate a cache with a complete mailbox. */
final class MailReader {
 final MaintenanceContext context;MailReader(MaintenanceContext c){context=c;}
 JSONObject inspect(int index)throws Exception{
  context.active();int loaded=0,candidates=0,special=0;JSONArray ids=new JSONArray();int type=MailPolicy.type(index);
  try(GameMemory m=new GameMemory(context.controller.cache)){
   if(!m.open("UIMailNew4")||m.state.getInt("modalWindowCount")!=1)throw new IOException("Unexpected Mail context");
   long view=m.path(MailPolicy.VIEW.substring(0,MailPolicy.VIEW.length()-1)),ctrl=GameMemory.f(view,"ctrl"),group=m.path(MailPolicy.VIEW+"_toggles/#"+index+"/_mailChannelType");
   if(GameMemory.number(group,"id")!=index||GameMemory.number(group,"type")!=type||GameMemory.number(ctrl,"currentTab")!=type)throw new IOException("Mail selected group mismatch");
   if(GameMemory.bool(view,"selectBatch")||GameMemory.bool(view,"isChoose"))throw new IOException("Mail batch selection active");
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("DataCenter/MailFacade/_repository/_mailDict"))){if((row.tag&15)!=5)continue;long h=GameMemory.f(row.raw,"_header");if(GameMemory.number(h,"groupId")!=type)continue;
    String id=GameMemory.string(h,"uid"),recipient=GameMemory.string(h,"toUser");if(MailPolicy.placeholder(id,recipient,GameMemory.number(h,"type"),GameMemory.bool(h,"hasReward"),GameMemory.number(h,"rewardStatus"),GameMemory.number(h,"deal")))continue;if(!id.matches("[0-9]{1,20}")||!recipient.equals(context.uid))throw new IOException("Mail identity/recipient mismatch");loaded++;
    boolean has=GameMemory.bool(h,"hasReward");long state=GameMemory.number(h,"rewardStatus"),deal=GameMemory.number(h,"deal"),expiry=GameMemory.number(h,"expireTime");
    if(MailPolicy.ordinaryCandidate(has,state,deal,expiry,System.currentTimeMillis())){candidates++;ids.put(id);}else if(has&&state==0)special++;
   }
  }
  JSONObject label=context.input.action(new JSONObject().put("action","ui-bounds").put("path",MailPolicy.VIEW+"_toggles/#"+index+"/check_text").put("stateOnly",true));
  if(!label.getBoolean("active")||!MailPolicy.name(index).equals(label.optString("text")))throw new IOException("Mail selected tab label mismatch");
  return new JSONObject().put("tab",MailPolicy.name(index)).put("groupType",type).put("loadedHeaders",loaded).put("ordinaryCandidates",candidates).put("specialPending",special).put("candidateIds",ids).put("completeMailboxProven",false);
 }
}
