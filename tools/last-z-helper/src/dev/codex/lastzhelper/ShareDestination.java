package dev.codex.lastzhelper;
/** One saved destination for every sharing button; attack is a separate action. */
public final class ShareDestination {
 public static final String WORLD="world",GROUP="group";
 public static String checked(String destination){if(!WORLD.equals(destination)&&!GROUP.equals(destination))throw new IllegalArgumentException("Choose Trucks group or World Chat");return destination;}
 public static String resolve(String action,String destination){
  boolean group=GROUP.equals(checked(destination));
  if(action.equals("truck-share-2"))return group?"truck-group-2":"truck-world";
  if(action.equals("truck-share-3"))return group?"truck-dm":"truck-world-3";
  if(action.equals("truck-share-cargo"))return group?"truck-group-cargo":"truck-world-cargo";
  if(action.equals("bounties-share"))return group?"bounties-group":"bounties";
  return action;
 }
}
