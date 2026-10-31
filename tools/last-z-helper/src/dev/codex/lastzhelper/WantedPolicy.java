package dev.codex.lastzhelper;
/** Finished personal rewards only; this policy never authorizes dispatch or stealing. */
final class WantedPolicy {
 static final String VIEW="UIManagerInstance/windows/UIActivityCenterTable/View/";
 static final String PANEL=VIEW+"panelComponentList/400001";
 static String classify(long uuid,long rewarded,long start,long end,long now,boolean steal,String owner,long point){
  if(steal||point!=0||owner==null||!owner.isEmpty())return "EXCLUDED";
  if(uuid<=0||rewarded<0||rewarded>1||start<=0||end<=start||now<=0||start>now)return "BLOCKED";
  if(rewarded==1)return "ALREADY_RECEIVED";
  return end<=now?"READY_INSPECTION_ONLY":"WAITING";
 }
}
