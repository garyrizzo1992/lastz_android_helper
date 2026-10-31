package dev.codex.lastzhelper;
/** Template inspection rules only. No result authorizes a training start. */
final class TrainingStartPolicy {
 static int type(String unit){if(unit==null||!unit.matches("107[012][0-9]{2}"))throw new IllegalArgumentException("Unsupported unit family");return unit.charAt(3)=='0'?1:unit.charAt(3)=='1'?8:9;}
 static String buildingRequirement(long actualBuilding,long expectedBuilding,long currentLevel,long requiredLevel){if(actualBuilding!=expectedBuilding||currentLevel<1||requiredLevel<1)return "UNRESOLVED";return currentLevel>=requiredLevel?"MET":"LOCKED_BY_BUILDING_LEVEL";}
 static boolean validCost(long type,long count){return type>0&&count>=0;}
}
