package dev.codex.lastzhelper;
/** Combat entry controls are exclusive to the explicit main-account attack mode. */
final class CombatPolicy {
 static boolean protectedControl(String path,String label){return path.contains("/UILWTrainScene/View/infoPanel/goBtn")||path.contains("/UIWorldPoint/View/buildBtnCells/")||path.contains("/UIPVEScene/View/btn_start")||path.contains("/UIPVEScene/View/onekeyFillHeroBtn")||label.equalsIgnoreCase("Plunder")||label.equalsIgnoreCase("Plunder!");}
 static boolean allowed(String mode,String uid){return "truck-attack".equals(mode)&&TruckPolicy.MAIN_UID.equals(uid);}
}
