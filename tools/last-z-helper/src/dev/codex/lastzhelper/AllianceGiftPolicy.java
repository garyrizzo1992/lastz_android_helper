package dev.codex.lastzhelper;
final class AllianceGiftPolicy {
 static final String VIEW="UIManagerInstance/windows/UIAllianceGift/View/";
 static String name(int tab){if(tab==1)return "Common";if(tab==2)return "Rare";throw new IllegalArgumentException("Unknown gift tab");}
 static int rewardType(int tab){name(tab);return tab==1?2:1;}
 static boolean allowed(String path,boolean preview){return path.equals("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/alliance_btn")||AllianceMenu.path(path)||path.equals(AllianceHelpPolicy.MAIN+"_closeBtn")||path.equals(VIEW+"close_btn")||path.equals(VIEW+"toogles/#1")||path.equals(VIEW+"toogles/#2")||(!preview&&path.equals(VIEW+"get_all_btn"));}
 static boolean claimable(int count,boolean active,boolean enabled,String caption,boolean busy,boolean ready){return count>0&&active&&enabled&&"Claim All".equals(caption)&&!busy&&ready;}
 static boolean received(long beforeState,long afterState,long receivedAt){return beforeState==0&&afterState==1&&receivedAt>0;}
}
