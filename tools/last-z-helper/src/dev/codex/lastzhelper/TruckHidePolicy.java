package dev.codex.lastzhelper;
/** Mandatory game filter: never blindly toggle a checkbox. */
public final class TruckHidePolicy {
 public static final String PATH="UIManagerInstance/windows/UILWTrainScene/View/outSeverToggle";
 public static boolean enabled(int luaTag){if(luaTag==17)return true;if(luaTag==1)return false;throw new IllegalArgumentException("Unknown Hide trucks of this state setting");}
 public static boolean shouldClick(boolean saved,boolean checked){if(saved!=checked)throw new IllegalArgumentException("Truck filter memory and checkbox disagree; no click sent");return !checked;}
 public static boolean ready(boolean saved,Boolean checked,boolean active,boolean interactable){return checked!=null&&saved==checked.booleanValue()&&(checked.booleanValue()||(active&&interactable));}
}
