package dev.codex.lastzhelper;
import android.content.*;import java.io.*;import org.json.*;
/** Live and preview use explicit actions, independent of truck preview preferences. */
final class BotRun {
 static JSONObject options(Context c,boolean preview)throws Exception{
  RotationProfiles profiles=new RotationProfiles(new File(c.getFilesDir(),"rotation-profiles.json"));JSONArray selected=new JSONArray();for(JSONObject p:profiles.selected())selected.put(new JSONObject(p.toString()));
  return JobRunner.options(c).put("dryRun",preview).put("visitMinutes",RotationPolicy.minutes(c.getSharedPreferences("runs",0).getInt("rotationMinutes",20))).put("selectedProfiles",selected);
 }
 static void service(Context c,boolean preview)throws Exception{c.startForegroundService(new Intent(c,HelperService.class).setAction("maintenance-rotation").putExtra("options",options(c,preview).toString()));}
}
