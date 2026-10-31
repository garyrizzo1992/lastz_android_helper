package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Per-run bridge; feature workflows stay out of the legacy controller. */
final class MaintenanceContext {
 final AutomationController controller;final DeviceInput input;final MaintenanceStore store;final String uid;final boolean preview;
 MaintenanceFeature activeFeature;
 MaintenanceContext(AutomationController c)throws Exception{controller=c;input=c.input;uid=MaintenanceSchedule.uid(StateProbe.pinnedUid);preview=c.dryRun;store=new MaintenanceStore(new File(c.dir,"maintenance-state.json"));
  input.requestGuard=request->{if(activeFeature!=null&&!activeFeature.requiresInstrumentation())throw new IOException("Memory-only feature cannot start instrumentation");String action=request.optString("action"),path=request.optString("path");if(action.equals("inspect")||action.equals("ui-metadata")||action.equals("ui-bounds")||action.equals("map-region")||action.equals("map-point")||action.equals("state-errors"))return;if(AllianceMenu.path(path)&& (activeFeature==null||!AllianceMenu.requestAllowed(activeFeature.id(),request.optInt("allianceMenuType"),request.optString("allianceMenuName"))||!request.optString("allianceMenuGuild").matches("[a-f0-9]{32}")))throw new IOException("Alliance menu is outside the selected feature");if(activeFeature==null||request.has("child")||request.has("label")||!activeFeature.permitsInput(action,path,preview))throw new IOException("Maintenance action is outside the selected feature's permissions");};
 }
 void active()throws Exception{input.check(true);if(!uid.equals(StateProbe.pinnedUid))throw new IOException("Maintenance character changed");}
 void event(String feature,String message)throws Exception{active();System.out.println(new JSONObject().put("event","maintenance-progress").put("feature",feature).put("accountUid",uid).put("message",message).put("timestampMs",System.currentTimeMillis()).put("dryRun",preview));System.out.flush();}
 void base()throws Exception{active();try(GameMemory m=new GameMemory(controller.cache)){if(m.state.getInt("sceneId")==1&&m.state.getInt("modalWindowCount")==0)return;}controller.worldReady();ControlProbe.navigate(input,1);}
 String begin(String feature,String period,String target,JSONObject before)throws Exception{active();if(preview)throw new IOException("Preview cannot begin a consuming maintenance action");return store.begin(uid,feature,period,target,System.currentTimeMillis(),before);}
}
