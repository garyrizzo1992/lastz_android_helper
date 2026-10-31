package dev.codex.lastzhelper;
/** One bounded unit of maintenance. A consuming action must use the attempt barrier. */
interface MaintenanceFeature {
 String id();
 int priority();
 default boolean requiresInstrumentation(){return true;}
 default boolean deferInstrumentationUntilAction(){return false;}
 default boolean permitsInput(String action,String path,boolean preview){return false;}
 MaintenanceResult run(MaintenanceContext context)throws Exception;
}
