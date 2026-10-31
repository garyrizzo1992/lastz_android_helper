package dev.codex.lastzhelper;
public final class TruckCargoTests {
 static int checks;
 static void check(boolean condition,String name){checks++;if(!condition)throw new AssertionError(name);}
 static void rejects(Runnable action,String name){boolean rejected=false;try{action.run();}catch(IllegalArgumentException expected){rejected=true;}check(rejected,name);}
 public static void main(String[] args){
  String box="253102;7;2",frag="210454;7;1";
  check(TruckCargo.icons(TruckCargo.MODULE_BOX,7,2)==1,"two items inside one icon count as one box");
  int[] four=TruckCargo.payload(box+"|"+box+"|"+box+"|"+box);
  check(four[0]==0&&four[1]==4,"four box icons are four, not eight");
  check(TruckCargo.valuable(four[0],four[1]),"four boxes without fragments qualify");
  check(TruckCargo.valuable(1,3),"one orange plus three boxes");
  check(TruckCargo.valuable(2,2),"two orange plus two boxes");
  check(TruckCargo.valuable(3,0)&&TruckCargo.valuable(4,0),"three or more orange without boxes");
  check(TruckCargo.valuable(2,3)&&TruckCargo.valuable(1,4),"higher counts qualify");
  check(!TruckCargo.valuable(0,3)&&!TruckCargo.valuable(1,2)&&!TruckCargo.valuable(2,1),"near misses excluded");
  int[] mixed=TruckCargo.payload(frag+"|"+frag+"|"+box+"|"+box+"|210453;7;10|252014;7;3|1;1;3000000");
  check(mixed[0]==2&&mixed[1]==2,"other fragment grades/chest types/resources excluded");
  check(TruckCargo.payload("210454;7;9")[0]==1,"fragment slot remains one regardless of quantity");
  check(TruckCargo.icons(TruckCargo.MODULE_BOX,7,0)==0,"zero remaining reward excluded");
  rejects(()->TruckCargo.payload("253102;7;1"),"unexpected one-item module icon rejected");
  rejects(()->TruckCargo.payload("253102;7;4"),"merged four-item icon not inferred as two icons");
  rejects(()->TruckCargo.payload("253102;1;2"),"wrong reward type rejected");
  rejects(()->TruckCargo.payload("253102;7;-2"),"negative count rejected");
  rejects(()->TruckCargo.payload("253102;7"),"malformed payload rejected");
  rejects(()->TruckCargo.valuable(-1,4),"unknown fragment count rejected");
  for(String destination:new String[]{ShareDestination.WORLD,ShareDestination.GROUP}){
   boolean group=destination.equals(ShareDestination.GROUP);
   check(ShareDestination.resolve("truck-share-2",destination).equals(group?"truck-group-2":"truck-world"),"two-plus destination");
   check(ShareDestination.resolve("truck-share-3",destination).equals(group?"truck-dm":"truck-world-3"),"three-plus destination");
   String mode=ShareDestination.resolve("truck-share-cargo",destination);
   check(mode.equals(group?"truck-group-cargo":"truck-world-cargo"),"cargo destination");
   check(ShareDestination.resolve("bounties-share",destination).equals(group?"bounties-group":"bounties"),"bounty destination");
   check(ShareDestination.resolve("truck-attack",destination).equals("truck-attack"),"destination does not alter attack");
   for(int[] counts:new int[][]{{0,4},{1,3},{2,2},{3,0},{4,0}})
    check(TruckPolicy.classify(mode,5,counts[0],100000000,440000000,counts[1]).equals(group?"PRIVATE_SHARE_ELIGIBLE":"WORLD_SHARE_ELIGIBLE"),"each cargo combination in both destinations");
   check(TruckPolicy.classify(mode,4,1,100000000,440000000,2).equals("SKIP"),"near miss not shared");
   check(TruckPolicy.classify(mode,3,0,100000000,440000000,4).equals("SKIP_GRADE"),"other truck grades excluded");
   check(TruckPolicy.classify(mode,5,0,0,440000000,4).equals("UNKNOWN"),"known power required");
   check(!CombatPolicy.allowed(mode,TruckPolicy.MAIN_UID),"cargo sharing cannot attack");
   check(TruckPolicy.accountAllowed(mode,TruckPolicy.MAIN_UID),"main may post its group/world");
  }
  check(TruckPolicy.classify("truck-group-cargo",5,0,440000000,440000000,4).equals("SKIP"),"group power limit remains strict");
  check(TruckPolicy.classify("truck-world-cargo",5,0,900000000,440000000,4).equals("WORLD_SHARE_ELIGIBLE"),"World ignores attack limit");
  check(TruckPolicy.classify("truck-group-2",4,2,100000000,440000000,0).equals("PRIVATE_SHARE_ELIGIBLE"),"two-plus can now share to group");
  check(TruckPolicy.classify("truck-world-cargo",5,3,100000000,440000000).equals("UNKNOWN"),"missing box metadata cannot guess");
  rejects(()->ShareDestination.resolve("truck-share-cargo","private"),"unknown destination rejected");
  System.out.println("Passed "+checks+" cargo and shared-destination checks");
 }
}
