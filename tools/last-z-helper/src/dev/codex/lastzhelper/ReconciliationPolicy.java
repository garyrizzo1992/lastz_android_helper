package dev.codex.lastzhelper;
import org.json.*;
/** Exact read-only receipts for the existing workers that expose stable identities. */
final class ReconciliationPolicy {
 static boolean wanted(JSONObject before,JSONObject after)throws Exception{
  return before.getString("uuid").matches("[1-9][0-9]{0,23}")&&before.getLong("configId")>0&&before.getLong("startTime")>0&&before.getLong("completionTime")>=before.getLong("startTime")&&before.getString("uuid").equals(after.getString("uuid"))&&before.getLong("configId")==after.getLong("configId")&&before.getLong("startTime")==after.getLong("startTime")&&before.getLong("completionTime")==after.getLong("completionTime")&&before.getLong("rewarded")==0&&after.getLong("rewarded")==1;
 }
 static boolean training(JSONObject before,JSONObject after)throws Exception{
  int quantity=before.getInt("quantity");long free=before.getLong("freeUnits"),train=before.getLong("trainingUnits");
  return quantity>0&&free>=0&&free<=Long.MAX_VALUE-quantity&&train>=quantity&&after.getLong("freeUnits")>=0&&after.getLong("trainingUnits")>=0&&"READY_TO_COLLECT".equals(before.getString("decision"))&&before.getString("queueId").equals(after.getString("queueId"))&&before.getString("unitId").equals(after.getString("unitId"))&&before.getString("buildingUid").equals(after.getString("buildingUid"))&&after.getInt("queueState")==0&&after.getLong("freeUnits")==free+quantity&&train-after.getLong("trainingUnits")==quantity;
 }
}
