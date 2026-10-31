package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Only verified production maintenance tasks; no scanners, combat or inspection tools. */
final class MaintenanceRegistry {
 static MaintenanceFeature create(String id){
  switch(id){
   case "vip":return new VipFeature();
   case "alliance_help":return new AllianceHelpFeature();
   case "alliance_gifts":return new AllianceGiftFeature();
   case "training_collection":return new TrainingCollectionFeature();
   case "wanted_finished_reward":return new WantedFeature();
   default:throw new IllegalArgumentException("No production worker registered for "+id);
  }
 }
 static List<MaintenanceFeature> selected(JSONObject flags)throws Exception{
  List<MaintenanceFeature> out=new ArrayList<>();
  for(String id:RotationPolicy.FEATURES)if(flags.getBoolean(id))out.add(create(id));
  return out;
 }
}
