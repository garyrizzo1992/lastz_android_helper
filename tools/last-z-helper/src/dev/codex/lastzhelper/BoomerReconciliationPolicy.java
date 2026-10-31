package dev.codex.lastzhelper;
import org.json.*;
/** Expiry receipt for one recorded activation window; never authorizes replay. */
final class BoomerReconciliationPolicy {
 static boolean receipt(JSONObject before,JSONObject after)throws Exception{
  long requested=before.getLong("activationRequestedMs"),observed=before.getLong("observedMs"),expiry=after.getLong("expiryMs"),now=after.getLong("observedMs");
  if(requested<=0||observed<=0||observed>requested||requested-observed>15000||requested>Long.MAX_VALUE-BoomerPolicy.DURATION-20000||now<requested||expiry<=now)return false;
  if(!"INACTIVE".equals(before.getString("state"))||before.getLong("expiryMs")!=0||before.getLong("timerSeconds")!=-2||!"ACTIVE".equals(after.getString("state"))||!"40005".equals(before.getString("activityId"))||!before.getString("activityId").equals(after.getString("activityId"))||!before.getString("accountUid").matches("[0-9]{8,24}")||!before.getString("accountUid").equals(after.getString("accountUid")))return false;
  JSONArray a=before.getJSONArray("options"),b=after.getJSONArray("options");if(a.length()!=2||b.length()!=2)return false;boolean selected=false;
  for(int i=0;i<2;i++){JSONObject x=a.getJSONObject(i),y=b.getJSONObject(i);if(x.getInt("type")!=i+1||y.getInt("type")!=i+1||!(x.get("selected") instanceof Boolean)||!(y.get("selected") instanceof Boolean)||x.getBoolean("selected")!=y.getBoolean("selected"))return false;selected|=x.getBoolean("selected");}
  long timer=after.getLong("timerSeconds");return selected&&timer>=0&&Math.abs((expiry-now)/1000-timer)<=5&&expiry>=requested+BoomerPolicy.DURATION-5000&&expiry<=requested+BoomerPolicy.DURATION+20000;
 }
}
