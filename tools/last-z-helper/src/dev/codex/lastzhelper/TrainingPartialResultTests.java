package dev.codex.lastzhelper;
import org.json.*;
/** Android JSON fixture only: no files, game reads, injection or input. */
public final class TrainingPartialResultTests {
 public static void main(String[] args)throws Exception{
  TrainingCollectionFeature feature=new TrainingCollectionFeature();JSONArray receipts=new JSONArray().put(new JSONObject().put("queueId","1256861592788680957").put("quantity",145));int checks=0;
  for(MaintenanceResult.Outcome outcome:new MaintenanceResult.Outcome[]{MaintenanceResult.Outcome.BLOCKED,MaintenanceResult.Outcome.FAILED,MaintenanceResult.Outcome.UNCERTAIN}){
   MaintenanceResult result=feature.partial(outcome,"stopped after one verified collection",1,receipts,123);
   if(result.outcome!=outcome||!"1".equals(result.evidence.get("collectedQueues"))||result.nextDueMs!=123)throw new AssertionError("Partial outcome/count lost");checks++;
   JSONArray saved=new JSONArray(result.evidence.get("receipts"));if(saved.length()!=1||!saved.getJSONObject(0).getString("queueId").equals("1256861592788680957")||saved.getJSONObject(0).getInt("quantity")!=145)throw new AssertionError("Verified receipt lost");checks++;
  }
  System.out.println("Passed "+checks+" partial-training result checks; no gameplay access");
 }
}
