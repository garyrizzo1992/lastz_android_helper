package dev.codex.lastzhelper;
/** Mutually exclusive user-selected truck modes. */
public final class TruckPolicy {
 public static final String MAIN_UID="2028198887000064",MAIN_NAME="Gaarix";
 public static boolean known(String mode){return groupMode(mode)||mode.equals("truck-attack")||worldMode(mode);}
 public static boolean worldMode(String mode){return mode.equals("truck-world")||mode.equals("truck-world-3")||mode.equals("truck-world-cargo");}
 public static boolean groupMode(String mode){return mode.equals("truck-dm")||mode.equals("truck-group-2")||mode.equals("truck-group-cargo");}
 public static boolean cargoMode(String mode){return mode.equals("truck-world-cargo")||mode.equals("truck-group-cargo");}
 public static String classify(String mode,int quality,int slots,long power,long limit){
  return classify(mode,quality,slots,power,limit,-1);
 }
 public static String classify(String mode,int quality,int slots,long power,long limit,int boxes){
  if(!known(mode))throw new IllegalArgumentException("Choose Share to trucks group, Attack on main, or Share to World");
  if(quality!=4&&quality!=5)return "SKIP_GRADE";
  if(slots<0)return "UNKNOWN";
  if(cargoMode(mode)){if(boxes<0)return "UNKNOWN";if(!TruckCargo.valuable(slots,boxes))return "SKIP";}
  else if(slots<(mode.equals("truck-world")||mode.equals("truck-group-2")?2:3))return "SKIP";
  if(worldMode(mode))return power>0?"WORLD_SHARE_ELIGIBLE":"UNKNOWN";
  if(groupMode(mode)){if(power<=0)return "UNKNOWN";return power<limit?"PRIVATE_SHARE_ELIGIBLE":"SKIP";}
  if(slots<3)return "SKIP";if(power<=0)return "UNKNOWN";if(power>=limit)return "SKIP";
  return mode.equals("truck-dm")?"PRIVATE_SHARE_ELIGIBLE":"ALERT_TARGET";
 }
 public static boolean accountAllowed(String mode,String uid){return mode.equals("truck-attack")?MAIN_UID.equals(uid):known(mode);}
 public static boolean unavailableCell(boolean dispatched,String phase,String action,String error){return !dispatched&&phase.equals("native_pre_dispatch")&&action.equals("ui-tap")&&(error.equals("Error: Exported control is hidden")||error.equals("Error: Exported control is disabled")||error.equals("Error: Control is outside visible screen"));}
 /** Explicit one-off diagnostic allowance; the normal classifier above remains at three. */
 public static String classifyTwoFragmentTest(int quality,int slots,long power,long limit){return classifySelectedTest(quality,slots,power,limit,2);}
 public static String classifySelectedTest(int quality,int slots,long power,long limit,int minimumSlots){if(minimumSlots<1||minimumSlots>3)throw new IllegalArgumentException("Diagnostic slot bound");if(quality!=4&&quality!=5)return "SKIP_GRADE";if(slots<0)return "UNKNOWN";if(slots<minimumSlots)return "SKIP";if(power<=0)return "UNKNOWN";return power<limit?"ALERT_TARGET":"SKIP";}
}
