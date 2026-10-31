package dev.codex.lastzhelper;
public final class RotationPolicyTests {
 static int checks;static void expect(boolean v,String m){if(!v)throw new AssertionError(m);checks++;}
 public static void main(String[] args){
  expect(RotationPolicy.FEATURES.length==5,"only five production maintenance features");expect(!RotationPolicy.feature("truck-attack")&&!RotationPolicy.feature("bounties")&&!RotationPolicy.feature("eight_hour_chest"),"scanners combat and quarantined chest excluded");
  expect(AllianceMenu.path(AllianceMenu.LIST+"/#7/_btn")&&!AllianceMenu.path(AllianceMenu.LIST+"/#0/_btn")&&!AllianceMenu.path(AllianceMenu.LIST+"/#65/_btn"),"bounded dynamic rows");
  expect(AllianceMenu.requestAllowed("alliance_help",3,"Help")&&!AllianceMenu.requestAllowed("alliance_help",4,"Alliance Gifts")&&!AllianceMenu.requestAllowed("alliance_gifts",3,"Help"),"row semantics stay within feature permissions");
  expect(RotationPolicy.minutes(20)==20,"legacy default");for(int n:new int[]{0,-1,121}){boolean rejected=false;try{RotationPolicy.minutes(n);}catch(IllegalArgumentException e){rejected=true;}expect(rejected,"invalid duration");}
  for(MaintenanceResult.Outcome o:MaintenanceResult.Outcome.values())expect(RotationPolicy.halt(o)==(o==MaintenanceResult.Outcome.BLOCKED||o==MaintenanceResult.Outcome.FAILED||o==MaintenanceResult.Outcome.UNCERTAIN),"halt policy "+o);
  MaintenanceResult done=MaintenanceResult.of(MaintenanceResult.Outcome.NOTHING_TO_DO,"none",0);expect(RotationPolicy.nextDue("wanted_finished_reward",done,1000)==901000,"Wanted zero due has bounded retry");expect(RotationPolicy.nextDue("alliance_help",done,1000)==61000,"no zero due polling");
  expect(RotationPolicy.nextDue("vip",MaintenanceResult.of(MaintenanceResult.Outcome.WAITING,"cooldown",5000000),1000)==5000000,"real cooldown retained");
  boolean rejected=false;try{RotationPolicy.nextDue("eight_hour_chest",done,1);}catch(IllegalArgumentException e){rejected=true;}expect(rejected,"unsupported task cannot enroll");System.out.println("Rotation policy: "+checks+" checks passed");
 }
}
