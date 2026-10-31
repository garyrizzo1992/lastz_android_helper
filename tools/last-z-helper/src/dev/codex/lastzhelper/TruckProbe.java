package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
public final class TruckProbe {
 static long field(long table,String key)throws Exception{return StateProbe.ptr(StateProbe.findField(table,key));}
 static String string(long table,String key)throws Exception{return StateProbe.luaString(field(table,key));}
 static String templateString(long table,String key)throws Exception{
  // Template fields are materialized lazily by Lua; read their backing row on a cold start.
  if(GameMemory.optional(table,key)!=0)return string(table,key);
  long descriptor=field(field(table,"indexData"),key);int column=0;
  for(TruckDiscoveryProbe.Value v:GameMemory.rows(descriptor))if(v.key.equals("#1"))column=(int)(v.tag==19?Double.longBitsToDouble(v.raw):v.raw);
  if(column<1||column>128)throw new IOException("Invalid template column "+key);
  return StateProbe.luaString(GameMemory.f(field(table,"lineData"),"#"+column));
 }
 static int[] cargoCounts(long data,String group)throws Exception{
  int[] counts=new int[4];long current=field(field(data,group),"cur");
  for(TruckDiscoveryProbe.Value row:TruckDiscoveryProbe.rows(current)){
   if((row.tag&15)!=5)continue;int type=(int)StateProbe.number(row.raw,"type");if(type!=7)continue;
   long value=field(row.raw,"value"),amount=StateProbe.number(value,"num");String id=string(value,"id");
   if(amount<0||amount>1000000000L)throw new IOException("Invalid reward quantity");
   int icon=TruckCargo.icons(id,type,amount);if(icon==0)continue;
   int offset=TruckCargo.ORANGE.equals(id)?0:2;counts[offset]+=icon;counts[offset+1]=Math.addExact(counts[offset+1],Math.toIntExact(amount));
  }return counts;
 }
 static int[] fragmentSlots(long data,String group)throws Exception{int[] c=cargoCounts(data,group);return new int[]{c[0],c[1]};}
 static final class ListLoading extends IOException{ListLoading(){super("No loaded enemy-truck records; wait for the list to load");}}
 static JSONArray readList(String cache)throws Exception{
  JSONObject state=StateProbe.snapshot(cache);long manager=StateProbe.pinnedManager;
  try{
   StateProbe.mem=new RandomAccessFile("/proc/"+state.getInt("pid")+"/mem","r");
   long globals=StateProbe.globalsAt(manager),windows=field(field(globals,"UIManagerInstance"),"windows"),window=field(windows,"UILWTrainScene");
   if(StateProbe.number(window,"State")!=2||state.getInt("modalWindowCount")!=1||StateProbe.number(field(window,"View"),"curTab")!=1)throw new IOException("Open Others' Trucks and close other dialogs first");
   long dc=field(globals,"DataCenter"),rail=field(dc,"LWTrainDataManager"),list=field(rail,"enemyTrucks"),item=field(field(field(dc,"ItemTemplateManager"),"itemDic"),"210454");
   if(!"hero_fragment_orange".equals(templateString(item,"icon")))throw new IOException("Orange-fragment item mapping changed");
   long boxes=field(field(field(dc,"ItemTemplateManager"),"itemDic"),TruckCargo.MODULE_BOX);if(!TruckCargo.MODULE_ICON.equals(templateString(boxes,"icon")))throw new IOException("Lv.3 module chest item mapping changed");
   JSONArray result=new JSONArray();Set<String> ids=new HashSet<>();
   for(TruckDiscoveryProbe.Value row:TruckDiscoveryProbe.rows(list)){
    if((row.tag&15)!=5)continue;long data=row.raw;String id=Long.toString(StateProbe.number(data,"uuid"));if(!ids.add(id))throw new IOException("Duplicate truck identity in snapshot");
    int quality=(int)StateProbe.number(data,"quality");long power=StateProbe.number(data,"power");int[] base=cargoCounts(data,"baseGoods"),extra=cargoCounts(data,"extraGoods");int count=base[0]+extra[0];
    String ownerUid="";try{long owner=GameMemory.optional(data,"ownerId");if(owner==0)owner=GameMemory.optional(data,"uid");if(owner!=0)ownerUid=StateProbe.luaString(owner);}catch(IOException ignored){}
    result.put(new JSONObject().put("id",id).put("owner",string(data,"name")).put("ownerUid",ownerUid).put("serverId",StateProbe.number(data,"serverId")).put("grade",quality==4?"purple":quality==5?"yellow":"other").put("quality",quality).put("power",power).put("orangeFragmentSlots",count).put("orangeFragmentQuantity",base[1]+extra[1]).put("moduleBoxIcons",base[2]+extra[2]).put("moduleBoxQuantity",base[3]+extra[3]).put("decision",TruckRules.classify(quality,count,power)));
   }
   if(result.length()==0)throw new ListLoading();
   if(!state.getString("processStart").equals(StateProbe.start(String.valueOf(state.getInt("pid")))))throw new IOException("Game restarted during truck read");
   return result;
  }finally{if(StateProbe.mem!=null){StateProbe.mem.close();StateProbe.mem=null;}}
 }
 static Map<String,String> identities(JSONArray a)throws Exception{Map<String,String> m=new TreeMap<>();for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);m.put(o.getString("id"),o.getInt("quality")+":"+o.getLong("power")+":"+o.getInt("orangeFragmentSlots")+":"+o.getInt("orangeFragmentQuantity")+":"+o.getInt("moduleBoxIcons")+":"+o.getInt("moduleBoxQuantity"));}return m;}
 static JSONArray readReadyList(String cache)throws Exception{long until=System.nanoTime()+3000000000L;while(true)try{return readList(cache);}catch(ListLoading loading){if(System.nanoTime()>=until)throw loading;StateProbe.cancelCheck();Thread.sleep(100);}}
 public static JSONObject snapshot(String cache)throws Exception{return snapshot(cache,TruckRules.LIMIT);}
 public static JSONObject snapshot(String cache,long powerLimit)throws Exception{JSONArray first=readReadyList(cache),second=null;boolean stable=false;for(int i=0;i<4;i++){Thread.sleep(200);second=readReadyList(cache);if(identities(first).equals(identities(second))){stable=true;break;}first=second;}if(!stable)throw new IOException("Truck records changed repeatedly; no match reported");JSONArray targets=new JSONArray(),share=new JSONArray(),candidates=new JSONArray();for(int i=0;i<second.length();i++){JSONObject t=second.getJSONObject(i);t.put("decision",TruckRules.classify(t.getInt("quality"),t.getInt("orangeFragmentSlots"),t.getLong("power"),powerLimit));if(t.getInt("quality")==4||t.getInt("quality")==5)candidates.put(t);if(t.getString("decision").equals("ALERT_TARGET"))targets.put(t);if(t.getString("decision").equals("WORLD_SHARE_ELIGIBLE"))share.put(t);}return new JSONObject().put("ok",true).put("source","loaded enemy-truck Lua state").put("readOnly",true).put("individualTrucksOpened",false).put("stableObservations",2).put("loadedTruckCount",second.length()).put("loadedTrucks",second).put("candidateCount",candidates.length()).put("powerLimit",powerLimit).put("orangeFragmentItemId","210454").put("counting","separate current reward slots; quantity reported separately").put("alertTargets",targets).put("worldShareEligible",share).put("candidates",candidates).put("worldChatPostsSent",0).put("timestampMs",System.currentTimeMillis());}
 public static void main(String[] args){try{System.out.println(snapshot(args[0]).toString(2));}catch(Throwable e){try{System.out.println(new JSONObject().put("ok",false).put("error",e.toString()).toString(2));}catch(Exception ignored){}System.exit(1);}}
}
