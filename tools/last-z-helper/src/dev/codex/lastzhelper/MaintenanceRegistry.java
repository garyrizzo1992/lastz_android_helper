package dev.codex.lastzhelper;
import java.util.*;import org.json.*;
/** Only verified production maintenance tasks; no scanners, combat or inspection tools. */
final class MaintenanceRegistry {
 static List<MaintenanceFeature> selected(JSONObject flags)throws Exception{List<MaintenanceFeature> out=new ArrayList<>();for(String id:RotationPolicy.FEATURES){if(!flags.getBoolean(id))continue;out.add(id.equals("vip")?new VipFeature():id.equals("alliance_help")?new AllianceHelpFeature():id.equals("alliance_gifts")?new AllianceGiftFeature():id.equals("training_collection")?new TrainingCollectionFeature():new WantedFeature());}return out;}
}
