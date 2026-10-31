package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** One serial maintenance pass; does not launch accounts or start background loops. */
final class MaintenanceRunner {
 static List<MaintenanceResult> run(MaintenanceContext c,List<MaintenanceFeature> features,boolean enabledOnly)throws Exception{
  return run(c,features,enabledOnly,false);
 }
 static List<MaintenanceResult> run(MaintenanceContext c,List<MaintenanceFeature> features,boolean enabledOnly,boolean rotation)throws Exception{
  return run(c,features,enabledOnly,rotation,false);
 }
 static List<MaintenanceResult> run(MaintenanceContext c,List<MaintenanceFeature> features,boolean enabledOnly,boolean rotation,boolean retry)throws Exception{
  List<MaintenanceFeature> ordered=new ArrayList<>(features);Set<String> ids=new HashSet<>();for(MaintenanceFeature f:ordered)if(!ids.add(MaintenanceSchedule.feature(f.id())))throw new IllegalArgumentException("Duplicate maintenance feature");ordered.sort(Comparator.comparingInt(MaintenanceFeature::priority));List<MaintenanceResult> results=new ArrayList<>();
  for(MaintenanceFeature feature:ordered){c.active();if(enabledOnly&&(!c.store.enabled(c.uid,feature.id())||!c.store.due(c.uid,feature.id(),System.currentTimeMillis())))continue;
   if(rotation&&!retry&&!c.preview&&!c.store.unresolved(c.uid,feature.id())&&!c.store.due(c.uid,feature.id(),System.currentTimeMillis()))continue;
   MaintenanceResult result;c.activeFeature=feature;try{if(c.store.unresolved(c.uid,feature.id()))result=MaintenanceResult.of(MaintenanceResult.Outcome.UNCERTAIN,"Previous operation requires read-only reconciliation",0);else result=feature.run(c);}finally{c.activeFeature=null;}
   if(c.preview&&result.outcome==MaintenanceResult.Outcome.COMPLETED)throw new IllegalStateException("Preview must not report completed maintenance");
   if(rotation&&!c.preview)result=new MaintenanceResult(result.outcome,result.reason,RotationPolicy.nextDue(feature.id(),result,System.currentTimeMillis()),result.evidence);
   if(!c.preview)c.store.record(c.uid,feature.id(),result,System.currentTimeMillis());results.add(result);
   c.event(feature.id(),result.reason);System.out.println(new JSONObject().put("event","maintenance-result").put("accountUid",c.uid).put("feature",feature.id()).put("outcome",result.outcome.name()).put("reason",result.reason).put("nextDueMs",result.nextDueMs).put("evidence",new JSONObject(result.evidence)).put("dryRun",c.preview));System.out.flush();
   if(result.uncertain()||(rotation&&RotationPolicy.halt(result.outcome)))break;
  }return results;
 }
}
