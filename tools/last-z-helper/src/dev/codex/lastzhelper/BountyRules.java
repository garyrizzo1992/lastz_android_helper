package dev.codex.lastzhelper;
public final class BountyRules {
 public static boolean qualifies(int boxes,int taken,int maximum){return (boxes==12||boxes==15)&&taken>=0&&maximum>0&&taken<maximum;}
 public static int itemQuantity(String rewards,int item){
  int total=0;for(String part:rewards.split("\\|")){String[] a=part.split(";");if(a.length>=2&&Integer.parseInt(a[0])==item)total+=Integer.parseInt(a[1]);}return total;
 }
}
