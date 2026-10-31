package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** At most three completed training collections; never starts training, healing or upgrades. */
final class TrainingCollectionFeature implements MaintenanceFeature {
 public String id(){return "training_collection";}public int priority(){return 60;}
 public boolean deferInstrumentationUntilAction(){return true;}
 public boolean permitsInput(String action,String path,boolean preview){return path.isEmpty()&&(action.equals("training-geometry-preview")||(!preview&&action.equals("training-collect")));}
 JSONObject current(MaintenanceContext context,String id)throws Exception{JSONArray rows=TrainingReader.read(context.controller.cache).getJSONArray("queues");for(int i=0;i<rows.length();i++)if(rows.getJSONObject(i).getString("queueId").equals(id))return rows.getJSONObject(i);throw new IOException("Training queue disappeared");}
 public MaintenanceResult run(MaintenanceContext context)throws Exception{
  if(context.preview)return new TrainingGeometryInspectionFeature().run(context);String pending=null;JSONObject target=null;int claimed=0;boolean compatibleSurfaceChecked=false;JSONArray receipts=new JSONArray();
  try{
   JSONArray rows=TrainingReader.read(context.controller.cache).getJSONArray("queues");
   for(int i=0;i<rows.length()&&claimed<3;i++){
    JSONObject q=rows.getJSONObject(i);if(!q.getString("decision").equals("READY_TO_COLLECT"))continue;target=current(context,q.getString("queueId"));if(!target.getString("decision").equals("READY_TO_COLLECT"))continue;
    if(!compatibleSurfaceChecked){context.input.foreground();compatibleSurfaceChecked=true;}
    long end=target.getLong("endTime"),free=target.getLong("freeUnits"),train=target.getLong("trainingUnits");int quantity=target.getInt("quantity");String id=target.getString("queueId"),unit=target.getString("unitId");
    pending=context.begin(id(),"end_"+end,"queue_"+id,target);
    context.input.action(new JSONObject().put("action","training-collect").put("trainingQueueId",id).put("trainingBuildingUid",target.getString("buildingUid")).put("trainingEnd",end).put("trainingPayload",unit+";"+quantity+";0").put("expectedTrainingCount",train).put("expectedFreeCount",free));
    long until=System.currentTimeMillis()+12000;JSONObject after=null;
    while(System.currentTimeMillis()<until){context.input.pause(200);try(GameMemory m=new GameMemory(context.controller.cache)){long queue=m.path("DataCenter/QueueDataManager/queueDic/#"+id),army=m.path("DataCenter/ArmyManager/allArmy/"+unit);if(GameMemory.number(queue,"uuid")!=Long.parseLong(id)||!unit.equals(GameMemory.string(army,"id")))throw new IOException("Training receipt identity changed");int state=(int)GameMemory.number(queue,"state");long newFree=GameMemory.number(army,"free"),newTrain=GameMemory.number(army,"train");if(TrainingPolicy.collected(state,free,newFree,train,newTrain,quantity)){after=new JSONObject().put("queueId",id).put("unitId",unit).put("queueState",state).put("quantity",quantity).put("beforeFree",free).put("afterFree",newFree).put("beforeTraining",train).put("afterTraining",newTrain);break;}}}
    if(after==null)throw new IOException("Training collection queue/inventory receipt not confirmed");context.store.verified(context.uid,pending,System.currentTimeMillis(),after);pending=null;claimed++;receipts.put(after);
   }
   Map<String,String> evidence=new LinkedHashMap<>();evidence.put("receipts",receipts.toString());evidence.put("collectedQueues",Integer.toString(claimed));return new MaintenanceResult(claimed>0?MaintenanceResult.Outcome.COMPLETED:MaintenanceResult.Outcome.NOTHING_TO_DO,"Completed training collected from "+claimed+" queues; running queues unchanged",System.currentTimeMillis()+300000,evidence);
  }catch(InterruptedException e){throw e;}catch(Exception e){if(pending!=null&&e instanceof DeviceInput.PreDispatchRejected){JSONObject fresh=current(context,target.getString("queueId"));if(fresh.getString("decision").equals("READY_TO_COLLECT")&&fresh.getLong("endTime")==target.getLong("endTime")){context.store.cancelBeforeInput(context.uid,pending,new JSONObject().put("receipt",((DeviceInput.PreDispatchRejected)e).receipt).put("gameTimestampUnchanged",true));pending=null;return partial(MaintenanceResult.Outcome.BLOCKED,"Training input rejected before dispatch after "+claimed+" verified collections; attempt retained, no automatic retry",claimed,receipts,System.currentTimeMillis()+900000);}}
   if(pending!=null){context.store.uncertain(context.uid,pending,e.toString());return partial(MaintenanceResult.Outcome.UNCERTAIN,"Training attempt saved after "+claimed+" verified collections; no automatic retry: "+e.getMessage(),claimed,receipts,0);}return partial(MaintenanceResult.Outcome.FAILED,"Training collection stopped after "+claimed+" verified collections: "+e.getMessage(),claimed,receipts,System.currentTimeMillis()+900000);
  }
 }
 MaintenanceResult partial(MaintenanceResult.Outcome outcome,String reason,int claimed,JSONArray receipts,long due){Map<String,String> evidence=new LinkedHashMap<>();evidence.put("collectedQueues",Integer.toString(claimed));evidence.put("receipts",receipts.toString());return new MaintenanceResult(outcome,reason,due,evidence);}

}
