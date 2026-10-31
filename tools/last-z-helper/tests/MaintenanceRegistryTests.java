package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Adding an ID must never silently run another feature's consuming worker. */
public final class MaintenanceRegistryTests {
 static int checks;static void expect(boolean value,String why){if(!value)throw new AssertionError(why);checks++;}
 public static void main(String[]args)throws Exception{
  JSONObject flags=new JSONObject();for(String id:RotationPolicy.FEATURES){flags.put(id,true);expect(MaintenanceRegistry.create(id).id().equals(id),"Registry preserves exact feature identity: "+id);}
  List<MaintenanceFeature> all=MaintenanceRegistry.selected(flags);expect(all.size()==RotationPolicy.FEATURES.length,"Every enabled production feature selected");
  for(int i=0;i<all.size();i++)expect(all.get(i).id().equals(RotationPolicy.FEATURES[i]),"Exact configured order/identity");
  for(String id:RotationPolicy.FEATURES)flags.put(id,false);expect(MaintenanceRegistry.selected(flags).isEmpty(),"Disabled features never select a worker");
  for(String id:new String[]{"unknown_future_feature","boomer_auto_join",""}){boolean rejected=false;try{MaintenanceRegistry.create(id);}catch(IllegalArgumentException expected){rejected=true;}expect(rejected,"Unavailable feature cannot fall back to Wanted: "+id);}
  flags.put("vip",true);List<MaintenanceFeature> one=MaintenanceRegistry.selected(flags);expect(one.size()==1&&one.get(0).id().equals("vip"),"One opt-in cannot execute disabled Wanted");
  System.out.println("Production registry: "+checks+" checks passed; no unknown-worker fallback");
 }
}
