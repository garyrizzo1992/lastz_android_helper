package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Read-only queue/building/bubble/army join using exact native integer identities. */
final class TrainingReader {
 static JSONObject read(String cache)throws Exception{
  try(GameMemory m=new GameMemory(cache)){
   if(m.state.getInt("sceneId")!=1||m.state.getInt("modalWindowCount")!=0)throw new IOException("Training inspection requires clear base");
   long types=m.path("NewQueueType"),states=m.path("NewQueueState");if(GameMemory.number(types,"CarSoldier")!=1||GameMemory.number(types,"FootSoldier")!=8||GameMemory.number(types,"BowSoldier")!=9||GameMemory.number(states,"Finish")!=3||GameMemory.number(states,"Work")!=2||GameMemory.number(states,"Free")!=0)throw new IOException("Training enums changed");
   List<JSONObject> rows=new ArrayList<>();int excluded=0;
   for(TruckDiscoveryProbe.Value row:GameMemory.rows(m.path("DataCenter/QueueDataManager/queueDic"))){if((row.tag&15)!=5)continue;long q=row.raw;int type=(int)GameMemory.number(q,"type");if(!TrainingPolicy.supported(type)){excluded++;continue;}long id=GameMemory.number(q,"uuid"),func=GameMemory.number(q,"funcUuid"),start=GameMemory.number(q,"startTime"),end=GameMemory.number(q,"endTime");int state=(int)GameMemory.number(q,"state");if(id<=0||!row.key.equals("#"+id)||func<=0)throw new IOException("Queue/building identity invalid");long build=m.path("DataCenter/BuildManager/allBuilding/#"+func);if(GameMemory.number(build,"uuid")!=func)throw new IOException("Building identity changed");
    String unit="";int count=0;long free=0,train=0;boolean matches=false;if(state!=0){TrainingPolicy.Item item=TrainingPolicy.item(type,GameMemory.string(q,"itemId"));unit=item.id;count=item.count;long army=m.path("DataCenter/ArmyManager/allArmy/"+unit);if(!unit.equals(GameMemory.string(army,"id")))throw new IOException("Army identity differs");free=GameMemory.number(army,"free");train=GameMemory.number(army,"train");if(free<0||train<0)throw new IOException("Invalid army counts");}
    if(state==3)try{long bubble=m.path("DataCenter/BuildBubbleManager/allBuildBubble/#"+func),param=GameMemory.f(bubble,"param");matches=GameMemory.bool(bubble,"isShow")&&GameMemory.number(param,"uuid")==id&&GameMemory.number(param,"funcUuid")==func;}catch(IOException ignored){}
    int building=(int)GameMemory.number(build,"itemId");String decision=TrainingPolicy.classify(type,state,m.state.getLong("timestampMs"),start,end,building,GameMemory.number(build,"unlock")==1,GameMemory.bool(build,"lockInput"),train,count,matches);
    rows.add(new JSONObject().put("queueId",Long.toString(id)).put("buildingUid",Long.toString(func)).put("type",type).put("state",state).put("startTime",start).put("endTime",end).put("buildingId",building).put("unitId",unit).put("quantity",count).put("freeUnits",state==0?JSONObject.NULL:free).put("trainingUnits",state==0?JSONObject.NULL:train).put("bubbleMatches",matches).put("decision",decision));
   }
   rows.sort(Comparator.comparingInt(o->o.optInt("type")));return new JSONObject().put("accountUid",m.state.getString("accountUid")).put("readOnly",true).put("excludedQueues",excluded).put("queues",new JSONArray(rows));
  }
 }
}
