package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
final class BountyReader {
 static final double ZOOM=746.01416015625;
 static class Template{int id,boxes,limit;Template(int i,int b,int l){id=i;boxes=b;limit=l;}}
 final String cache;Map<Long,Template> templates;
 BountyReader(String cache){this.cache=cache;}
 static long array(long t,int n)throws Exception{return GameMemory.f(t,"#"+n);}
 int column(long index,String name)throws Exception{long t=GameMemory.f(index,name);for(TruckDiscoveryProbe.Value v:GameMemory.rows(t))if(v.key.equals("#1"))return (int)(v.tag==19?Double.longBitsToDouble(v.raw):v.raw);throw new IOException("Missing template column "+name);}
 void ensureTemplates(GameMemory m)throws Exception{
  if(templates!=null)return;Map<Long,Template> found=new HashMap<>();
  long t=m.path("package/loaded/LuaDatatable.aps_dispatch_tasks"),idx=GameMemory.f(t,"index");int rc=column(idx,"steal_reward_show"),lc=column(idx,"steal_maxtimes");
  for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(t,"data")))if((row.tag&15)==5){long id=(long)Double.parseDouble(row.key.replace("#",""));String rewards=StateProbe.luaString(array(row.raw,rc));long limitAddr=0;int limit=0;for(TruckDiscoveryProbe.Value v:GameMemory.rows(row.raw))if(v.key.equals("#"+lc))limit=(int)(v.tag==19?Double.longBitsToDouble(v.raw):v.raw);found.put(id,new Template((int)id,BountyRules.itemQuantity(rewards,252006),limit));}
  if(found.isEmpty())throw new IOException("Bounty templates unavailable");templates=found;
 }
 JSONObject snapshot()throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   ensureTemplates(m);long wm=m.path("DataCenter/WorldPointManager"),camera=m.path("SceneManager/World/Camera"),pos=GameMemory.f(wm,"reqPos");
   long target=GameMemory.f(wm,"curCameraTarget");double worldX=GameMemory.decimal(target,"x"),worldZ=GameMemory.decimal(target,"z");int tileX=WorldCoordinates.x(worldX,worldZ),tileY=WorldCoordinates.y(worldZ);
   JSONArray list=new JSONArray();Set<String> ids=new HashSet<>();
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(GameMemory.f(wm,"allViewPoints")))if((row.tag&15)==5){
    long t=row.raw;if(GameMemory.number(t,"pointType")!=22)continue;
    long info=GameMemory.f(t,"pointInfo"),task=GameMemory.f(info,"dispatchMission"),xy=GameMemory.f(t,"mainIndexV2");String id=Long.toString(GameMemory.number(info,"uuid"));if(!ids.add(id))continue;
    long mission=GameMemory.number(task,"missionId");Template meta=templates.get(mission);if(meta==null)throw new IOException("Unknown dispatch mission "+mission);
    int taken=0;for(TruckDiscoveryProbe.Value user:GameMemory.rows(GameMemory.f(task,"stealUids")))if((user.tag&15)!=0)taken++;
    list.put(new JSONObject().put("uuid",id).put("server",GameMemory.number(info,"serverId")).put("x",GameMemory.number(xy,"x")).put("y",GameMemory.number(xy,"y")).put("missionId",mission).put("boxes",meta.boxes).put("taken",taken).put("maximum",meta.limit).put("doubleReward",GameMemory.number(task,"doubleReward")).put("finishTime",GameMemory.number(task,"finishTime")));
   }
   return new JSONObject().put("state",m.state).put("server",GameMemory.number(wm,"aoiServerId")).put("gameTime",(long)GameMemory.decimal(wm,"time")).put("x",tileX).put("y",tileY).put("requestX",GameMemory.number(pos,"x")).put("requestY",GameMemory.number(pos,"y")).put("lod",GameMemory.number(wm,"lodLv")).put("height",GameMemory.decimal(camera,"_lastHeight")).put("bounties",list);
  }
 }
 JSONObject find(String uuid)throws Exception{JSONArray a=snapshot().getJSONArray("bounties");for(int i=0;i<a.length();i++)if(uuid.equals(a.getJSONObject(i).getString("uuid")))return a.getJSONObject(i);return null;}
 public static void main(String[] args)throws Exception{System.out.println(new BountyReader(args[0]).snapshot().toString(2));}
}
