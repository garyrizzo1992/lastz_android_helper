package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Private explicit enrollment. No credentials and no inferred main/bot selection. */
final class RotationProfiles {
 final File file;final JSONObject data;final JSONArray profiles;
 RotationProfiles(File file)throws Exception{this(file,file.exists()?new JSONObject(StateProbe.text(file.getPath())):new JSONObject().put("schema",1).put("profiles",new JSONArray()));}
 RotationProfiles(File file,JSONObject source)throws Exception{this.file=file;data=new JSONObject(source.toString());if(data.getInt("schema")!=1)throw new IOException("Unknown rotation profiles schema");profiles=data.getJSONArray("profiles");Set<String> uids=new HashSet<>(),routes=new HashSet<>();for(int n=0;n<profiles.length();n++){JSONObject p=profiles.getJSONObject(n);String uid=MaintenanceSchedule.uid(p.getString("uid"));RotationShortcut s=RotationShortcut.from(p.getJSONObject("launch"));if(!uids.add(uid)||!routes.add(s.id))throw new IOException("Duplicate rotation character/shortcut");p.getBoolean("selected");JSONObject f=p.getJSONObject("features");for(String id:RotationPolicy.FEATURES){if(!f.has(id))f.put(id,true);f.getBoolean(id);}if(f.length()!=RotationPolicy.FEATURES.length)throw new IOException("Unknown rotation feature");}}
 void enroll(RotationShortcut route,JSONObject state)throws Exception{
  String uid=MaintenanceSchedule.uid(state.getString("accountUid"));JSONObject old=null;for(int n=0;n<profiles.length();n++){JSONObject p=profiles.getJSONObject(n);if(p.getJSONObject("launch").getString("shortcutId").equals(route.id)){if(!p.getString("uid").equals(uid))throw new IOException("Shortcut character changed; remove old profile explicitly before reenrollment");old=p;}else if(p.getString("uid").equals(uid))throw new IOException("Two shortcuts resolved to the same character; no automatic mapping");}
  if(old==null){JSONObject f=new JSONObject();for(String id:RotationPolicy.FEATURES)f.put(id,true);old=new JSONObject().put("uid",uid).put("selected",false).put("features",f);profiles.put(old);}
  old.put("name",state.getString("accountName")).put("launch",route.json()).put("verifiedAtMs",System.currentTimeMillis());save();
 }
 List<JSONObject> selected()throws Exception{List<JSONObject> selected=new ArrayList<>();for(int i=0;i<profiles.length();i++){JSONObject p=profiles.getJSONObject(i);if(p.getBoolean("selected")){boolean any=false;for(String f:RotationPolicy.FEATURES)any|=p.getJSONObject("features").getBoolean(f);if(!any)throw new IOException("Choose a feature for "+p.getString("name"));selected.add(p);}}if(selected.isEmpty())throw new IOException("Set up games and select at least one account");return selected;}
 void save()throws Exception{RotationFiles.write(file,data);}
}
