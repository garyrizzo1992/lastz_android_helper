package dev.codex.lastzhelper;
/** Free alliance help only; activation and other alliance functions are excluded. */
final class AllianceHelpPolicy {
 static final String MAIN="UIManagerInstance/windows/UIAllianceMainTable/View/";
 static final String VIEW="UIManagerInstance/windows/UIAllianceHelp/View/";
 static boolean allowed(String path,boolean preview){return path.equals("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/alliance_btn")||AllianceMenu.path(path)||path.equals(MAIN+"_closeBtn")||path.equals(VIEW+"close_btn")||(!preview&&path.equals(VIEW+"help_btn"));}
 static boolean eligible(long count,boolean active,boolean interactable,String caption){return count>0&&count<=8192&&active&&interactable&&"Help All".equals(caption);}
 static boolean verified(long beforeCount,long afterCount,long beforePoints,long afterPoints,int newHandled){return beforeCount>0&&afterCount>=0&&afterCount<beforeCount&&(afterPoints>beforePoints||newHandled>0);}
}
