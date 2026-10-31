package dev.codex.lastzhelper;
import org.json.JSONObject;
/** Receipt acquisition may navigate, but activation is forbidden even in a live context. */
final class BoomerReceiptNavigation implements MaintenanceFeature {
 public String id(){return "boomer_auto_join";}public int priority(){return 90;}
 public boolean permitsInput(String action,String path,boolean preview){return BoomerNavigationPolicy.permits(action,path,true);}
 public boolean permitsRequest(JSONObject request,boolean preview){
  if(request.has("label")||request.has("parent"))return false;
  if(request.has("child"))return BoomerNavigationPolicy.card(request.optString("eventCardPath"))&&BoomerNavigationPolicy.carousel(request.optString("action"),request.optString("path"),request.optString("child"),request.optString("direction"),request.optBoolean("eventCarousel"));
  return permitsInput(request.optString("action"),request.optString("path"),true);
 }
 public MaintenanceResult run(MaintenanceContext context){throw new UnsupportedOperationException("Receipt acquisition is not a production worker");}
}
