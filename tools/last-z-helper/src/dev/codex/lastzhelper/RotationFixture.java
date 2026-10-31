package dev.codex.lastzhelper;
import java.io.*;import java.util.*;import org.json.*;
/** Isolated Android JSON/profile/shortcut tests. No launching, game memory or injection. */
public final class RotationFixture {
 static int checks;static void expect(boolean v,String m){if(!v)throw new AssertionError(m);checks++;}
 interface Checked{void run()throws Exception;}static void rejects(Checked c)throws Exception{boolean bad=false;try{c.run();}catch(Exception e){bad=true;}expect(bad,"invalid state rejected");}
 public static void main(String[] args)throws Exception{
  String export="ShortcutInfo {id=Game one, flags=0x8a\npackageName=com.lbe.parallel.intl\ndisabledReason=[Not disabled]\nintents=[Intent { act=com.lbe.parallel.ACTION_LAUNCH_PACKAGE cmp=com.lbe.parallel.intl/com.lbe.parallel.ui.LaunchDelegateActivity }/PersistableBundle[{EXTRA_LAUNCH_UID=1, EXTRA_LAUNCH_PACKAGE=com.readygo.barrel.gp}]]\n";
  RotationShortcut route=RotationShortcut.parse(export).get(0);expect(route.clone==1&&route.id.equals("Game one"),"parse exact registered route");expect(Arrays.asList(route.launch()).contains("1"),"launch uses exported clone");rejects(()->RotationShortcut.parse(export+export));rejects(()->RotationShortcut.parse(export.replace("Not disabled","disabled")));rejects(()->RotationShortcut.parse(export.replace("EXTRA_LAUNCH_UID=1","EXTRA_LAUNCH_UID=1, unknown=2")));rejects(()->RotationShortcut.parse(export.replace("LaunchDelegateActivity }/","WrongActivity }/")));
  expect(RotationController.cloneInMaps("/data/data/com.lbe.parallel.intl/parallel_intl/1/com.readygo.barrel.gp/files/a\n/data/media/0/Android/data/com.lbe.parallel.intl/parallel_intl/1/com.readygo.barrel.gp/files/b")==1,"matching clone mapped twice");rejects(()->RotationController.cloneInMaps("unproven"));rejects(()->RotationController.cloneInMaps("/parallel_intl/1/com.readygo.barrel.gp/a /parallel_intl/2/com.readygo.barrel.gp/a"));
  JSONObject deferred=WantedReader.deferred(false,"fixture unloaded");expect(deferred.getBoolean("inspectionDeferred")&&!deferred.getBoolean("serverCompletenessProven"),"hidden Wanted is deferred, never complete");expect(!deferred.getBoolean("noReadyInLoadedRecords")&&!deferred.getBoolean("cachePreviouslyLoaded"),"unloaded records cannot prove no rewards");expect(WantedReader.deferred(true,"fixture empty").getJSONArray("tasks").length()==0,"empty cache preserves uninspected state");
  File dir=new File("/data/local/tmp/lastz-rotation-fixture-"+UUID.randomUUID());if(!dir.mkdir())throw new IOException("fixture mkdir");File file=new File(dir,"profiles.json");
  try{RotationProfiles p=new RotationProfiles(file);rejects(()->p.selected());JSONObject state=new JSONObject().put("accountUid","2059765822000064").put("accountName","Fixture");p.enroll(route,state);expect(!p.profiles.getJSONObject(0).getBoolean("selected"),"new accounts never auto-selected");expect(new RotationProfiles(file).profiles.length()==1,"profile reload");p.profiles.getJSONObject(0).put("selected",true);p.save();expect(new RotationProfiles(file).selected().size()==1,"selection survives restart");
   rejects(()->p.enroll(route,new JSONObject().put("accountUid","2028198887000064").put("accountName","Changed")));rejects(()->p.enroll(new RotationShortcut("Other",route.component,route.action,2),state));
   JSONObject f=p.profiles.getJSONObject(0).getJSONObject("features");for(String id:RotationPolicy.FEATURES)f.put(id,false);rejects(()->p.selected());f.put("vip",true);expect(MaintenanceRegistry.selected(f).size()==1&&MaintenanceRegistry.selected(f).get(0).id().equals("vip"),"registry follows per-UID flags");p.save();
   p.profiles.getJSONObject(0).getJSONObject("features").put("truck-attack",true);p.save();rejects(()->new RotationProfiles(file));
   ShareLedger.atomic(file,new JSONObject().put("schema",999).put("profiles",new JSONArray()));rejects(()->new RotationProfiles(file));
  }finally{for(File f:dir.listFiles())f.delete();dir.delete();}
  if(args.length>0){List<RotationShortcut> live=RotationShortcut.parse(StateProbe.text(args[0]));JSONArray routes=new JSONArray();for(RotationShortcut s:live)routes.put(s.json());System.out.println(new JSONObject().put("liveRegisteredShortcuts",routes));}
  System.out.println(new JSONObject().put("checks",checks).put("ok",true).put("gameInputs",0).put("gameMemoryReads",0));
 }
}
