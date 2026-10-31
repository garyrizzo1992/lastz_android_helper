package dev.codex.lastzhelper;
/** Distinct UI group and transport-channel identities; inspection currently permits no claims. */
final class MailPolicy {
 static final String VIEW="UIManagerInstance/windows/UIMailNew4/View/";
 static final String ENTRY="UIManagerInstance/windows/MainUI_SU/View/bottomLayer/mail_btn_slg";
 static int type(int index){int[] types={10,2,4,1,17,5};if(index<1||index>types.length)throw new IllegalArgumentException("Unknown mail tab");return types[index-1];}
 static String name(int index){String[] names={"Report","Jungle","Alliance","System","Recharge","Favorite"};type(index);return names[index-1];}
 static boolean inspectionControl(String path){if(path.equals(ENTRY)||path.equals(VIEW+"_btnClose"))return true;for(int n=1;n<=6;n++)if(path.equals(VIEW+"_toggles/#"+n))return true;return false;}
 static boolean placeholder(String id,String recipient,long type,boolean reward,long status,long deal){return recipient.isEmpty()&&!reward&&status==1&&deal==0&&((id.equals("00000000-0000-1-0000-000000000000")&&type==73)||(id.equals("00000000-0000-2-0000-000000000000")&&type==997)||(id.equals("00000000-0000-3-0000-000000000000")&&type==1000));}
 static boolean ordinaryCandidate(boolean hasReward,long state,long deal,long expires,long now){return hasReward&&state==0&&deal==0&&expires>now;}
}
