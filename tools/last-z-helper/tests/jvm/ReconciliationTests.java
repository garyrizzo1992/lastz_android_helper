package dev.codex.lastzhelper;
import org.json.*;
public final class ReconciliationTests {
 static int checks;static void expect(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
 public static void main(String[] args)throws Exception{
  JSONObject before=new JSONObject().put("uuid","1234567890123456").put("configId",400001).put("startTime",1000).put("completionTime",2000).put("rewarded",0),after=new JSONObject(before.toString()).put("rewarded",1);
  expect(ReconciliationPolicy.wanted(before,after),"exact previously pending reward transition");for(String f:new String[]{"uuid","configId","startTime","completionTime","rewarded"}){JSONObject changed=new JSONObject(after.toString());changed.put(f,f.equals("uuid")?"9999999999999999":9999);expect(!ReconciliationPolicy.wanted(before,changed),"Wanted different "+f+" cannot reconcile");}expect(!ReconciliationPolicy.wanted(new JSONObject(before.toString()).put("rewarded",1),after),"already rewarded before-state is not a new transition");
  before=new JSONObject().put("queueId","123456789").put("buildingUid","987654321").put("unitId","107207").put("quantity",48).put("freeUnits",201).put("trainingUnits",48).put("decision","READY_TO_COLLECT");after=new JSONObject().put("queueId","123456789").put("buildingUid","987654321").put("unitId","107207").put("queueState",0).put("freeUnits",249).put("trainingUnits",0);
  expect(ReconciliationPolicy.training(before,after),"exact empty queue and army delta");for(String f:new String[]{"queueId","buildingUid","unitId","queueState","freeUnits","trainingUnits"}){JSONObject changed=new JSONObject(after.toString());changed.put(f,f.endsWith("Id")||f.equals("buildingUid")?"111111111":99);expect(!ReconciliationPolicy.training(before,changed),"training different "+f+" cannot reconcile");}
  expect(!ReconciliationPolicy.training(before,new JSONObject(after.toString()).put("freeUnits",250)),"extra army gain is ambiguous after interruption");expect(!ReconciliationPolicy.training(new JSONObject(before.toString()).put("decision","WAITING"),after),"running queue cannot reconcile as collection");expect(!ReconciliationPolicy.training(new JSONObject(before.toString()).put("freeUnits",Long.MAX_VALUE),after),"overflow cannot create a receipt");
  System.out.println("Read-only reconciliation: "+checks+" checks passed; exact identity/delta required");
 }
}
