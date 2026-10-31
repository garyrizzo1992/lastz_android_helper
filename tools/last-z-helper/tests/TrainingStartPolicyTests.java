package dev.codex.lastzhelper;
public final class TrainingStartPolicyTests {
 static int checks;static void expect(boolean b){if(!b)throw new AssertionError("check "+checks);checks++;}
 public static void main(String[] args){
  expect(TrainingStartPolicy.type("107007")==1);expect(TrainingStartPolicy.type("107107")==8);expect(TrainingStartPolicy.type("107207")==9);
  for(String value:new String[]{"107307","107007;145;0","10707","107007/other",""})try{TrainingStartPolicy.type(value);throw new AssertionError("Invalid unit accepted");}catch(IllegalArgumentException expected){checks++;}
  expect(TrainingStartPolicy.buildingRequirement(423000,423000,25,24).equals("MET"));expect(TrainingStartPolicy.buildingRequirement(423000,423000,25,27).equals("LOCKED_BY_BUILDING_LEVEL"));expect(TrainingStartPolicy.buildingRequirement(423000,424000,25,24).equals("UNRESOLVED"));expect(TrainingStartPolicy.buildingRequirement(423000,423000,0,24).equals("UNRESOLVED"));
  expect(TrainingStartPolicy.validCost(1,2950));expect(!TrainingStartPolicy.validCost(0,2950));expect(!TrainingStartPolicy.validCost(1,-1));
  TrainingStartInspectionFeature feature=new TrainingStartInspectionFeature();expect(!feature.requiresInstrumentation());expect(!feature.permitsInput("ui-tap","",true));expect(!feature.permitsInput("training-collect","",false));
  System.out.println("Passed "+checks+" training start inspection policy checks");
 }
}
