package dev.codex.lastzhelper;
/** Exact non-consuming Event Center route. No arbitrary descendants or labels. */
final class BoomerNavigationPolicy {
 static final String HOME="UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn";
 static final String ENTRY="UIManagerInstance/windows/MainUI_SU/View/rightLayer/activityViewBtnSlg";
 static final String EVENT="UIManagerInstance/windows/UIActivityCenterTable/View/";
 static final String AUTO=EVENT+"panelComponentList/40005/autoBtnN";
 static final String DIALOG="UIManagerInstance/windows/UIAllianceAutoJoinRally/View/";
 static boolean card(String path){return path!=null&&path.matches("UIManagerInstance/windows/UIActivityCenterTable/View/groupItems/(?:[1-9][0-9]{0,15}|#[1-9][0-9]{0,4})/tabItems/40005/btn");}
 static String route(String path){
  if(HOME.equals(path))return "home";if(ENTRY.equals(path))return "entry";if(card(path))return "card";
  if(AUTO.equals(path))return "dialog";if((DIALOG+"closeBtnN").equals(path))return "close-dialog";
  if((EVENT+"bottomCloseBtn").equals(path))return "close-event";return "";
 }
 static boolean carousel(String action,String path,String child,String direction,boolean enabled){return enabled&&action.equals("ui-swipe")&&path.equals(EVENT+"tabScrollViewN")&&child.equals("Viewport")&&(direction.equals("left")||direction.equals("right"));}
 static boolean permits(String action,String path,boolean preview){return action.equals("ui-tap")&&(!route(path).isEmpty()||(!preview&&path.equals(DIALOG+"autoJoinBtnN")));}
}
