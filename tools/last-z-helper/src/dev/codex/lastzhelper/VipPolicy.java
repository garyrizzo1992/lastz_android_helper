package dev.codex.lastzhelper;
/** VIP free claims only. Activate, gift packs, shop and level purchases are not claims. */
final class VipPolicy {
 enum State {CLAIMABLE,COOLDOWN,BLOCKED}
 static boolean allowedControl(String path){return path.equals("UIManagerInstance/windows/MainUI_SU/View/topLayer/vip_btn")||path.equals("UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn")||path.equals("UIManagerInstance/windows/UIVip/View/box_btn")||path.equals("UIManagerInstance/windows/UIVip/View/free_btn")||path.equals("UIManagerInstance/windows/UIVip/View/close_btn")||path.equals("UIManagerInstance/windows/UIVIPRewardPopUp/View/return_btn");}
 static long countdown(String text){
  if(text==null)return -1;String value=text.replaceAll("<[^>]*>","").trim();if(!value.matches("[0-9]{1,2}:[0-5][0-9]:[0-5][0-9]"))return -1;String[] p=value.split(":");long seconds=Long.parseLong(p[0])*3600+Long.parseLong(p[1])*60+Long.parseLong(p[2]);return seconds>0&&seconds<=48*3600?seconds:-1;
 }
 static State state(boolean opened,boolean unopened,boolean buttonActive,boolean interactable,String caption,String timer,boolean freebies){
  if(opened==unopened)return State.BLOCKED;
  if(opened)return countdown(timer)>0?State.COOLDOWN:State.BLOCKED;
  String label=caption==null?"":caption.replaceAll("<[^>]*>","").trim();
  boolean freeLabel=label.equalsIgnoreCase("Claim")||label.equalsIgnoreCase("Free")||(freebies&&label.equals("0"));
  return buttonActive&&interactable&&freeLabel?State.CLAIMABLE:State.BLOCKED;
 }
 static long nextDue(long nowMs,long seconds){if(nowMs<0||seconds<1||seconds>48*3600)throw new IllegalArgumentException("Invalid VIP cooldown");return Math.addExact(nowMs,Math.multiplyExact(seconds,1000));}
 static String period(long nowMs,long previousReadyMs,long revision){if(nowMs<0||previousReadyMs<0||revision<=0)throw new IllegalArgumentException("Invalid VIP eligibility identity");if(previousReadyMs>0&&nowMs<previousReadyMs-2000)throw new IllegalStateException("VIP became claimable before the previous verified cooldown ended");return previousReadyMs>0?"after_"+previousReadyMs:"first_"+revision;}
}
