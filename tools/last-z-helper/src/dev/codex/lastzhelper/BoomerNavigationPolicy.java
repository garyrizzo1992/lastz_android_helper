package dev.codex.lastzhelper;
/** Exact non-consuming Event Center route. No arbitrary descendants or labels. */
final class BoomerNavigationPolicy {
 static final String ENTRY="UIManagerInstance/windows/MainUI_SU/View/rightLayer/activityViewBtnSlg";
 static final String EVENT="UIManagerInstance/windows/UIActivityCenterTable/View/";
 static final String CARD=EVENT+"groupItems/372337/tabItems/40005/btn";
 static final String AUTO=EVENT+"panelComponentList/40005/autoBtnN";
 static final String DIALOG="UIManagerInstance/windows/UIAllianceAutoJoinRally/View/";
 static String route(String path){
  if(ENTRY.equals(path))return "entry";if(CARD.equals(path))return "card";
  if(AUTO.equals(path))return "dialog";if((DIALOG+"closeBtnN").equals(path))return "close-dialog";
  if((EVENT+"bottomCloseBtn").equals(path))return "close-event";return "";
 }
 static boolean carousel(String action,String path,String child,String direction,boolean enabled){return enabled&&action.equals("ui-swipe")&&path.equals(EVENT+"tabScrollViewN")&&child.equals("Viewport")&&direction.equals("left");}
 static boolean permits(String action,String path,boolean preview){return action.equals("ui-tap")&&(!route(path).isEmpty()||(!preview&&path.equals(DIALOG+"autoJoinBtnN")));}
}
