package dev.codex.lastzhelper;

import java.io.*;
import java.util.*;
import org.json.*;

/**
 * Memory-only, allowlisted header-state snapshot, also when Mail is closed.
 * GameMemory may refresh the existing infrastructure discovery cache; no feature
 * outcomes, settings, history, subjects, bodies or attachments are written/read.
 */
public final class MailHeaderStateProbe {
 private static final int MAX_HEADERS=8192;
 private static final String REPOSITORY="DataCenter/MailFacade/_repository/_mailDict";

 static JSONObject read(String cache)throws Exception{
  JSONObject result;
  try(GameMemory memory=new GameMemory(cache)){
   String uid=MaintenanceSchedule.uid(memory.state.getString("accountUid"));
   long table=memory.path(REPOSITORY);requireTableBound(table,13,8192);
   List<TruckDiscoveryProbe.Value> repository=GameMemory.rows(table);
   if(repository.size()>MAX_HEADERS)throw new IOException("Mail header snapshot bound exceeded");
   List<JSONObject> headers=new ArrayList<>();Set<String> ids=new HashSet<>();int placeholders=0;
   for(TruckDiscoveryProbe.Value row:repository){
    StateProbe.cancelCheck();
    if((row.tag&15)!=5)throw new IOException("Unexpected Mail repository row type");
    long header=GameMemory.f(row.raw,"_header");requireTableBound(header,8,128);
    String id=string(header,"uid"),recipient=string(header,"toUser");
    boolean reward=bool(header,"hasReward");long rewardStatus=integer(header,"rewardStatus"),deal=integer(header,"deal"),type=integer(header,"type");
    MailHeaderProbePolicy.Identity identity=MailHeaderProbePolicy.identity(id,recipient,uid,type,reward,rewardStatus,deal);
    if(identity==MailHeaderProbePolicy.Identity.SYNTHETIC_PLACEHOLDER){placeholders++;continue;}
    if(identity!=MailHeaderProbePolicy.Identity.OWN||!ids.add(id))throw new IOException("Missing, foreign, unsupported or duplicate Mail header identity");
    headers.add(new JSONObject().put("uid",id).put("status",integer(header,"status")).put("rewardStatus",rewardStatus).put("hasReward",reward).put("deal",deal).put("expireTime",integer(header,"expireTime")).put("groupId",integer(header,"groupId")));
   }
   if(memory.path(REPOSITORY)!=table)throw new IOException("Mail repository changed during snapshot");
   StateProbe.verifyPinned();
   headers.sort(Comparator.comparing(header->header.optString("uid")));
   result=new JSONObject().put("ok",true).put("accountUid",uid).put("sampledAtMs",memory.state.getLong("timestampMs")).put("finishedAtMs",System.currentTimeMillis()).put("readOnly",true).put("memoryOnly",true).put("infrastructureCacheMayRefresh",true).put("enumSemanticsKnown",false).put("atomicSnapshot",false).put("mailOpen",memory.open("UIMailNew4")).put("loadedHeaders",headers.size()).put("syntheticPlaceholdersExcluded",placeholders).put("completeMailboxProven",false).put("headers",new JSONArray(headers));
  }
  return result;
 }

 private static void requireTableBound(long table,int maxLog,int maxArray)throws Exception{
  if(table==0||StateProbe.u8(table+11)>maxLog||(StateProbe.ptr(table+8)>>>32)>maxArray)throw new IOException("Mail snapshot table bound exceeded");
 }
 private static long integer(long owner,String key)throws Exception{
  long slot=StateProbe.findField(owner,key);if(StateProbe.u8(slot+8)!=3)throw new IOException("Expected exact Mail header integer: "+key);return StateProbe.ptr(slot);
 }
 private static boolean bool(long owner,String key)throws Exception{
  long slot=StateProbe.findField(owner,key);int tag=StateProbe.u8(slot+8);if(tag!=1&&tag!=17)throw new IOException("Expected explicit Mail header boolean: "+key);return tag==17;
 }
 private static String string(long owner,String key)throws Exception{
  long slot=StateProbe.findField(owner,key);if((StateProbe.u8(slot+8)&15)!=4)throw new IOException("Expected Mail header identity string: "+key);return StateProbe.luaString(StateProbe.ptr(slot));
 }

 public static void main(String[] args){
  try{
   if(args.length!=1||args[0].isEmpty())throw new IOException("Expected one existing discovery-cache path");
   System.out.println(read(args[0]));
  }catch(Throwable error){
   try{System.out.println(new JSONObject().put("ok",false).put("readOnly",true).put("enumSemanticsKnown",false).put("infrastructureCacheMayRefresh",true).put("error",error.toString()));}catch(Exception ignored){}
   System.exit(1);
  }
 }
}
