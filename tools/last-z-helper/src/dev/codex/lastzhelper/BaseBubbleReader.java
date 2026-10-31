package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Allowlisted own-base inventory. Does not resolve Unity objects or input. */
final class BaseBubbleReader {
 static long integer(long t,String key)throws Exception{long a=StateProbe.findField(t,key);if(StateProbe.u8(a+8)!=3)throw new IOException("Expected exact base-bubble integer: "+key);return StateProbe.ptr(a);}
 static String string(long t,String key)throws Exception{long a=StateProbe.findField(t,key);if((StateProbe.u8(a+8)&15)!=4)throw new IOException("Expected base inventory string: "+key);return StateProbe.luaString(StateProbe.ptr(a));}
 static boolean bool(long t,String key)throws Exception{long a=StateProbe.findField(t,key);int tag=StateProbe.u8(a+8);if(tag!=1&&tag!=17)throw new IOException("Expected explicit base-bubble boolean: "+key);return tag==17;}
 static List<TruckDiscoveryProbe.Value> rows(long t,int max)throws Exception{if(t==0||StateProbe.u8(t+11)>10||(StateProbe.ptr(t+8)>>>32)>max)throw new IOException("Base bubble table exceeds read bound");List<TruckDiscoveryProbe.Value> r=GameMemory.rows(t);if(r.size()>max)throw new IOException("Base bubble row bound");r.sort(Comparator.comparing(v->v.key));return r;}
 static boolean knownWindows(GameMemory m)throws Exception{Set<String> allowed=new HashSet<>(Arrays.asList("MainUI_SU","UIAlarm","TouchScreenEffect","UIMultiLanguageFloatingBall"));for(TruckDiscoveryProbe.Value r:rows(m.path("UIManagerInstance/windows"),128))if((r.tag&15)==5&&integer(r.raw,"State")==2&&!allowed.contains(r.key))return false;return true;}
 static void context(GameMemory m,String uid)throws Exception{if(!uid.equals(m.state.getString("accountUid"))||m.state.getInt("sceneId")!=1||m.state.getInt("levelId")!=10001||m.state.getInt("modalWindowCount")!=0||integer(m.path("SceneManager"),"CurrSceneID")!=1||integer(m.path("SceneManager"),"LevelId")!=10001||integer(m.path("UIManagerInstance/windowStack"),"length")!=0||!knownWindows(m))throw new IOException("Clear expected own base required for passive inspection");}
 static JSONObject scalar(long table,String key)throws Exception{
  Long a=MailCoverageReader.optionalSlot(table,key);if(a==null)return new JSONObject().put("presence","MISSING");int tag=StateProbe.u8(a+8);JSONObject out=new JSONObject().put("presence","PRESENT");
  if(tag==3)return out.put("kind","INTEGER").put("integerText",Long.toString(StateProbe.ptr(a)));
  if(tag==1||tag==17)return out.put("kind","BOOLEAN").put("boolean",tag==17);
  // Item payloads are data, not arbitrary text; do not retain unsupported strings.
  if((tag&15)==4){String value=StateProbe.luaString(StateProbe.ptr(a));if(value.matches("[0-9;]{1,64}"))return out.put("kind","NUMERIC_PAYLOAD").put("value",value);}
  return out.put("kind","UNSUPPORTED");
 }
 static JSONObject inventory(GameMemory m,JSONObject param)throws Exception{
  JSONObject field=param.optJSONObject("itemId"),out=new JSONObject().put("claimEligibilityProven",false);
  if(field==null)return out.put("status","NO_ITEM_REFERENCE");String item=field.optString("kind").equals("INTEGER")?field.optString("integerText"):field.optString("kind").equals("NUMERIC_PAYLOAD")?field.optString("value"):"";
  if(!item.matches("[1-9][0-9]{0,9}"))return out.put("status","NOT_A_SINGLE_ITEM_REFERENCE");
  long indexes=m.path("DataCenter/ItemData/ItemIdAndUuid");Long index=MailCoverageReader.optionalSlot(indexes,item);if(index==null)return out.put("status","ITEM_NOT_LOADED");if((StateProbe.u8(index+8)&15)!=4)throw new IOException("Own inventory item index type changed");String uuid=StateProbe.luaString(StateProbe.ptr(index));if(!uuid.matches("[1-9][0-9]{0,18}"))throw new IOException("Own inventory item UUID invalid");
  long info=m.path("DataCenter/ItemData/ItemInfos/"+uuid);long count=integer(info,"count");if(!BaseBubblePolicy.inventoryIdentity(item,uuid,string(info,"itemId"),string(info,"uuid"),count))throw new IOException("Own inventory identity/count mismatch");
  return out.put("status","EXACT_OWN_COUNTER_OBSERVED").put("itemId",item).put("itemUid",uuid).put("countText",Long.toString(count));
 }
 static JSONObject read(String cache,String uid)throws Exception{
  MaintenanceSchedule.uid(uid);try(GameMemory m=new GameMemory(cache)){
   context(m,uid);long owner=m.path("DataCenter/BuildBubbleManager/allBuildBubble"),buildings=m.path("DataCenter/BuildManager/allBuilding");JSONArray out=new JSONArray();int excluded=0;
   for(TruckDiscoveryProbe.Value row:rows(owner,128)){
    StateProbe.cancelCheck();if((row.tag&15)!=5||!row.key.matches("#[1-9][0-9]{0,18}"))throw new IOException("Base bubble dictionary identity invalid");long id=Long.parseLong(row.key.substring(1)),building=GameMemory.f(buildings,row.key),item=integer(building,"itemId");
    if(!BaseBubblePolicy.identity(row.key,integer(building,"uuid"),item))throw new IOException("Bubble is not joined to exact own building");if(bool(building,"isWorldBuild")){excluded++;continue;}
    long bubble=row.raw;JSONObject version=new JSONObject().put("level",integer(building,"level")).put("state",integer(building,"state")).put("unlock",integer(building,"unlock")).put("lockInput",bool(building,"lockInput")).put("lastCollectTimeText",Long.toString(integer(building,"lastCollectTime"))).put("produceEndTimeText",Long.toString(integer(building,"produceEndTime"))).put("productionSemanticsVerified",false);JSONObject param=new JSONObject();Long slot=MailCoverageReader.optionalSlot(bubble,"param");
    if(slot!=null&&(StateProbe.u8(slot+8)&15)==5){long value=StateProbe.ptr(slot);for(String key:new String[]{"uuid","funcUuid","itemId","count","type","buildUuid","queueUuid"})param.put(key,scalar(value,key));}else param.put("schema",slot==null?"MISSING":"UNSUPPORTED");
    String name="";try{long type=GameMemory.f(bubble,"_class_type");name=BaseBubblePolicy.boundedName(string(type,"__cname"));}catch(IOException ignored){}
    out.put(new JSONObject().put("buildingUid",Long.toString(id)).put("buildingItemId",item).put("buildingVersionObservation",version).put("bubbleClass",name).put("isShow",scalar(bubble,"isShow")).put("param",param).put("ownInventoryObservation",inventory(m,param)).put("classification","UNCLASSIFIED").put("claimEnabled",false).put("sensitiveBuildingExcludedFromEligibility",BaseBubblePolicy.sensitiveBuilding(item)).put("eligibility","NONE_PASSIVE_INSPECTION"));
   }
   if(m.path("DataCenter/BuildBubbleManager/allBuildBubble")!=owner)throw new IOException("Bubble inventory owner changed");StateProbe.verifyPinned();context(m,uid);
   return new JSONObject().put("accountUid",uid).put("readOnly",true).put("memoryOnly",true).put("claimEnabled",false).put("atomicSnapshot",false).put("infrastructureCacheMayRefresh",true).put("sampledAtMs",m.state.getLong("timestampMs")).put("worldBuildingsExcluded",excluded).put("bubbles",out);
  }
 }
}
