package dev.codex.lastzhelper;
import org.json.JSONObject;
/** One bounded unit of maintenance. A consuming action must use the attempt barrier. */
interface MaintenanceFeature {
 String id();
 int priority();
 default boolean requiresInstrumentation(){return true;}
 default boolean deferInstrumentationUntilAction(){return false;}
 default boolean permitsInput(String action,String path,boolean preview){return false;}
 default boolean permitsRequest(JSONObject request,boolean preview){return !request.has("child")&&!request.has("label")&&permitsInput(request.optString("action"),request.optString("path"),preview);}
 MaintenanceResult run(MaintenanceContext context)throws Exception;
}
