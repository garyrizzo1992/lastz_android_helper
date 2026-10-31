package dev.codex.lastzhelper;

import java.io.*;
import java.util.*;
import org.json.*;

/** Already-open Mail inspection only. No UI actions, game calls, claims or outcome writes. */
final class MailCoverageReader {
 static final String VIEW="UIManagerInstance/windows/UIMailNew4/View";
 static final String FACADE="DataCenter/MailFacade";
 static final int MAX_HEADERS=2048,MAX_MAP_ENTRIES=64,MAX_CHILD_FIELDS=24,MAX_CANDIDATE_IDS=64;
 static final String[] PAGING_MAPS={"_tabReachedEnd","_tabLocalExhausted","_tabOldestCursor","_tabBeforeTime","_loadContexts","_groupCountDict","_reqMoreTimeoutTimers","_reqMoreCallbacks"};
 static final String[] PAGING_SCALARS={"_headWindowDays","_headTime","_isUsingNewLoadLogic"};
 static final String[] REWARD_MAPS={"_rewardReqList","_claimingGroups"};

 static final class Observation {
  final JSONObject json;final boolean present,valid;final int entries;
  Observation(JSONObject json,boolean present,boolean valid,int entries){this.json=json;this.present=present;this.valid=valid;this.entries=entries;}
 }
 static final class Inventory {
  final JSONObject json;final String fingerprint;final int loaded,blocked;
  Inventory(JSONObject json,String fingerprint,int loaded,int blocked){this.json=json;this.fingerprint=fingerprint;this.loaded=loaded;this.blocked=blocked;}
 }
 static final class Paging {
  final JSONObject json;final boolean present,valid;final long requestEntries;
  Paging(JSONObject json,boolean present,boolean valid,long requestEntries){this.json=json;this.present=present;this.valid=valid;this.requestEntries=requestEntries;}
 }

 static JSONObject read(String cache,String expectedUid)throws Exception{
  MaintenanceSchedule.uid(expectedUid);
  JSONObject state,out;long firstView;int tab;Inventory inventory;Paging paging;
  try(GameMemory m=new GameMemory(cache)){
   state=m.state;
   if(!expectedUid.equals(state.getString("accountUid")))throw new IOException("Expected Mail inspection character is not active");
   out=base(expectedUid);
   if(!m.open("UIMailNew4"))return out.put("contextConfirmed",false).put("coverageState",MailCoveragePolicy.Coverage.UNINSPECTED.name()).put("reason","Mail must already be open; no navigation performed");
   if(state.getInt("modalWindowCount")!=1||!knownWindows(m))throw new IOException("Mail inspection requires the selected panel without unrelated overlays");
   firstView=m.path(VIEW);tab=selectedTab(firstView);requireUnselectedBatch(firstView);
   inventory=inventory(m,tab,expectedUid,state.getLong("timestampMs"));paging=paging(m,tab);
   long repository=m.path(FACADE+"/_repository");Observation count=scalarField(repository,"_count");
   out.put("contextConfirmed",true).put("groupType",tab).put("tab",tabName(tab)).put("sampledAtMs",state.getLong("timestampMs")).put("loaded",inventory.json).put("repositoryCountObserved",count.json).put("paging",paging.json);
  }
  boolean stable;
  try(GameMemory m=new GameMemory(cache)){
   stable=MailCoveragePolicy.sameIdentity(expectedUid,state.getString("processStart"),state.getInt("pid"),tab,m.state.getString("accountUid"),m.state.getString("processStart"),m.state.getInt("pid"),m.open("UIMailNew4")?selectedTab(m.path(VIEW)):-1);
   if(stable){stable=m.state.getInt("modalWindowCount")==1&&knownWindows(m)&&m.path(VIEW)==firstView;requireUnselectedBatch(m.path(VIEW));}
   if(stable){Inventory after=inventory(m,tab,expectedUid,state.getLong("timestampMs"));Paging afterPaging=paging(m,tab);stable=inventory.fingerprint.equals(after.fingerprint)&&paging.json.toString().equals(afterPaging.json.toString());}
  }
  MailCoveragePolicy.Coverage coverage=MailCoveragePolicy.coverage(true,stable,paging.valid&&inventory.blocked==0,inventory.loaded,paging.present,paging.requestEntries);
  return out.put("observedFieldsStableAcrossReads",stable).put("coverageState",coverage.name()).put("reason",coverage==MailCoveragePolicy.Coverage.BLOCKED?"Mail context or observations changed/are unsupported; completeness remains unproven":coverage==MailCoveragePolicy.Coverage.PENDING_METADATA_OBSERVED?"Request/callback/timer entries observed; their active-request semantics remain unproven":"Loaded/cache and paging metadata only; server history coverage remains unproven");
 }

 static JSONObject base(String uid)throws Exception{return new JSONObject().put("accountUid",uid).put("readOnly",true).put("memoryOnly",true).put("requiresAlreadyOpenMail",true).put("claimEnabled",false).put("completeMailboxProven",MailCoveragePolicy.completeMailboxProven()).put("serverCompletenessSemanticsVerified",false).put("dailyCompletionEligible",false);}
 static int selectedTab(long view)throws Exception{long value=integer(GameMemory.f(view,"ctrl"),"currentTab");for(int index=1;index<=6;index++)if(MailPolicy.type(index)==value){long group=GameMemory.f(GameMemory.f(GameMemory.f(view,"_toggles"),"#"+index),"_mailChannelType");if(integer(group,"id")!=index||integer(group,"type")!=value)throw new IOException("Mail selected group definition changed");return (int)value;}throw new IOException("Unsupported selected Mail group");}
 static String tabName(int tab){for(int index=1;index<=6;index++)if(MailPolicy.type(index)==tab)return MailPolicy.name(index);throw new IllegalArgumentException("Unknown selected tab");}
 static void requireUnselectedBatch(long view)throws Exception{if(bool(view,"selectBatch")||bool(view,"isChoose"))throw new IOException("Mail batch selection is active");}
 static boolean knownWindows(GameMemory m)throws Exception{Set<String> allowed=new HashSet<>(Arrays.asList("MainUI_SU","UIMultiLanguageFloatingBall","UIAlarm","TouchScreenEffect","UIMailNew4"));for(TruckDiscoveryProbe.Value row:boundedRows(m.path("UIManagerInstance/windows")))if((row.tag&15)==5&&integer(row.raw,"State")==2&&!allowed.contains(row.key))return false;return true;}

 static Inventory inventory(GameMemory m,int tab,String uid,long now)throws Exception{
  int loaded=0,ordinary=0,special=0,expired=0,received=0,noReward=0,blocked=0,placeholders=0;JSONArray candidates=new JSONArray();List<String> versions=new ArrayList<>();
  List<TruckDiscoveryProbe.Value> rows=boundedRows(m.path(FACADE+"/_repository/_mailDict"));
  if(rows.size()>MAX_HEADERS)throw new IOException("Mail header inventory bound exceeded");
  for(TruckDiscoveryProbe.Value row:rows){
   StateProbe.cancelCheck();if((row.tag&15)!=5)throw new IOException("Unexpected Mail repository row type");long h=GameMemory.f(row.raw,"_header");if(integer(h,"groupId")!=tab)continue;
   String id=GameMemory.string(h,"uid"),recipient=GameMemory.string(h,"toUser");boolean reward=bool(h,"hasReward");long rewardState=integer(h,"rewardStatus"),deal=integer(h,"deal"),expires=integer(h,"expireTime"),type=integer(h,"type");
   if(MailPolicy.placeholder(id,recipient,type,reward,rewardState,deal)){placeholders++;continue;}
   loaded++;versions.add(id+"|"+recipient+"|"+reward+"|"+rewardState+"|"+deal+"|"+expires+"|"+type);
   MailCoveragePolicy.Attachment decision=MailCoveragePolicy.attachment(id,recipient,uid,reward,rewardState,deal,expires,now);
   switch(decision){case ORDINARY_CANDIDATE:ordinary++;if(candidates.length()<MAX_CANDIDATE_IDS)candidates.put(id);break;case SPECIAL_PENDING:special++;break;case EXPIRED:expired++;break;case ALREADY_RECEIVED:received++;break;case NO_REWARD:noReward++;break;default:blocked++;}
  }
  Collections.sort(versions);JSONObject summary=new JSONObject().put("selectedGroupHeaders",loaded).put("ordinaryCandidates",ordinary).put("specialPendingExcluded",special).put("expiredOrdinary",expired).put("alreadyReceived",received).put("noReward",noReward).put("blockedHeaders",blocked).put("syntheticNoRewardHeadersExcluded",placeholders).put("candidateIds",candidates).put("candidateIdsTruncated",ordinary>MAX_CANDIDATE_IDS).put("cacheIsCompleteMailbox",false);
  return new Inventory(summary,versions.toString()+"|synthetic="+placeholders,loaded,blocked);
 }

 static Paging paging(GameMemory m,int tab)throws Exception{
  JSONObject json=new JSONObject(),fields=new JSONObject(),rewards=new JSONObject();long owner=m.path(FACADE+"/_pagingManager");boolean present=false,valid=true;long requestEntries=0;
  for(String name:PAGING_MAPS){StateProbe.cancelCheck();Observation value=mapField(owner,name,tab);fields.put(name,value.json);present|=value.present;valid&=value.valid;if(name.equals("_reqMoreTimeoutTimers")||name.equals("_reqMoreCallbacks"))requestEntries+=value.entries;}
  for(String name:PAGING_SCALARS){StateProbe.cancelCheck();Observation value=scalarField(owner,name);boolean expectedShape=!value.present||(name.equals("_isUsingNewLoadLogic")?"BOOLEAN".equals(value.json.optString("kind")):"INTEGER".equals(value.json.optString("kind")));fields.put(name,value.json.put("expectedKind",name.equals("_isUsingNewLoadLogic")?"BOOLEAN":"INTEGER").put("expectedKindObserved",expectedShape));present|=value.present;valid&=value.valid&&expectedShape;}
  Long rewardSlot=optionalSlot(m.path(FACADE),"_rewardManager");
  if(rewardSlot==null){rewards.put("presence","MISSING");valid=false;}else if((StateProbe.u8(rewardSlot+8)&15)!=5){rewards.put("presence","PRESENT").put("supportedShape",false);valid=false;}else{long rewardOwner=StateProbe.ptr(rewardSlot);for(String name:REWARD_MAPS){StateProbe.cancelCheck();Observation value=mapField(rewardOwner,name,tab);rewards.put(name,value.json);valid&=value.valid;requestEntries+=value.entries;}}
  return new Paging(json.put("fields",fields).put("rewardRequests",rewards).put("requestRelatedEntriesObserved",requestEntries).put("requestEntriesProveActiveRequest",false).put("mapKeyScopeVerified",false).put("localFlagsProveServerEnd",false),present,valid,requestEntries);
 }

 static Observation mapField(long owner,String name,int tab)throws Exception{
  Long slot=optionalSlot(owner,name);if(slot==null)return missing();int tag=StateProbe.u8(slot+8);JSONObject out=new JSONObject().put("presence","PRESENT").put("tag",tag);
  if((tag&15)!=5)return new Observation(out.put("supportedShape",false),true,false,0);
  long table=StateProbe.ptr(slot);List<TruckDiscoveryProbe.Value> rows=boundedRows(table);JSONArray entries=new JSONArray();boolean truncated=rows.size()>MAX_MAP_ENTRIES,childrenTruncated=false;
  int n=0;for(TruckDiscoveryProbe.Value row:rows){StateProbe.cancelCheck();if(n++>=MAX_MAP_ENTRIES)break;String keyType=keyType(table,row);JSONObject entry=value(row).put("key",row.key).put("keyType",keyType).put("matchesSelectedGroupKey",keyMatches(row.key,keyType,tab));
   if((row.tag&15)==5){List<TruckDiscoveryProbe.Value> children=boundedRows(row.raw);JSONArray childFields=new JSONArray();int count=0;for(TruckDiscoveryProbe.Value child:children){if(count++>=MAX_CHILD_FIELDS)break;if((child.tag&15)==4||(child.tag&15)==3||(child.tag&15)==1)childFields.put(value(child).put("key",child.key).put("keyType",keyType(row.raw,child)));}childrenTruncated|=children.size()>MAX_CHILD_FIELDS;entry.put("scalarFields",childFields).put("childFieldCountObserved",children.size()).put("childFieldsTruncated",children.size()>MAX_CHILD_FIELDS);}
   entries.put(entry);
  }
  return new Observation(out.put("supportedShape",true).put("entryCount",rows.size()).put("entries",entries).put("truncated",truncated).put("anyChildFieldsTruncated",childrenTruncated),true,!truncated&&!childrenTruncated,rows.size());
 }
 static Observation scalarField(long owner,String name)throws Exception{Long slot=optionalSlot(owner,name);if(slot==null)return missing();int tag=StateProbe.u8(slot+8);TruckDiscoveryProbe.Value row=new TruckDiscoveryProbe.Value(name,tag,slot,StateProbe.ptr(slot));boolean supported=tag==3||tag==19||tag==1||tag==17;return new Observation(value(row).put("presence","PRESENT").put("supportedShape",supported),true,supported,0);}
 static Observation missing()throws Exception{return new Observation(new JSONObject().put("presence","MISSING").put("valueKnown",false),false,true,0);}
 static Long optionalSlot(long owner,String name)throws Exception{try{return StateProbe.findField(owner,name);}catch(IOException e){if(("Lua field absent: "+name).equals(e.getMessage()))return null;throw e;}}
 static long integer(long owner,String name)throws Exception{long slot=StateProbe.findField(owner,name);if(StateProbe.u8(slot+8)!=3)throw new IOException("Expected exact Mail integer: "+name);return StateProbe.ptr(slot);}
 static boolean bool(long owner,String name)throws Exception{long slot=StateProbe.findField(owner,name);int tag=StateProbe.u8(slot+8);if(tag!=1&&tag!=17)throw new IOException("Expected explicit Mail boolean: "+name);return tag==17;}
 static List<TruckDiscoveryProbe.Value> boundedRows(long table)throws Exception{if(table==0||StateProbe.u8(table+11)>13||(StateProbe.ptr(table+8)>>>32)>8192)throw new IOException("Mail table read bound exceeded");List<TruckDiscoveryProbe.Value> rows=GameMemory.rows(table);rows.sort(Comparator.comparing((TruckDiscoveryProbe.Value v)->v.key).thenComparingInt(v->v.tag));return rows;}
 static JSONObject value(TruckDiscoveryProbe.Value row)throws Exception{JSONObject out=new JSONObject().put("tag",row.tag);if(row.tag==3)return out.put("kind","INTEGER").put("integerText",Long.toString(row.raw));if(row.tag==19){double v=Double.longBitsToDouble(row.raw);if(!Double.isFinite(v))throw new IOException("Nonfinite Mail scalar");return out.put("kind","FLOAT").put("number",v);}if(row.tag==1||row.tag==17)return out.put("kind","BOOLEAN").put("boolean",row.tag==17);if((row.tag&15)==4)return out.put("kind","STRING").put("string",StateProbe.luaString(row.raw));return out.put("kind",(row.tag&15)==5?"TABLE":"OTHER");}
 static String keyType(long table,TruckDiscoveryProbe.Value row)throws Exception{long array=StateProbe.ptr(table+16),size=StateProbe.ptr(table+8)>>>32;if(array!=0&&row.address>=array&&row.address<array+size*16)return "ARRAY_INTEGER";int tag=StateProbe.u8(row.address+9);return tag==3?"INTEGER":tag==19?"FLOAT":(tag&15)==4?"STRING":"OTHER";}
 static boolean keyMatches(String key,String kind,int tab){return ((kind.equals("INTEGER")||kind.equals("ARRAY_INTEGER"))&&key.equals("#"+tab))||(kind.equals("STRING")&&key.equals(Integer.toString(tab)));}
}
