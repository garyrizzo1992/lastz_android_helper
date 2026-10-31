package dev.codex.lastzhelper;
public final class TruckHideTests {
 static int checks;static void check(boolean result){checks++;if(!result)throw new AssertionError("Truck filter check "+checks);}
 static void rejects(Runnable action){boolean failed=false;try{action.run();}catch(IllegalArgumentException expected){failed=true;}check(failed);}
 public static void main(String[] args){check(TruckHidePolicy.enabled(17));check(!TruckHidePolicy.enabled(1));rejects(()->TruckHidePolicy.enabled(0));rejects(()->TruckHidePolicy.enabled(3));rejects(()->TruckHidePolicy.enabled(69));check(TruckHidePolicy.shouldClick(false,false));check(!TruckHidePolicy.shouldClick(true,true));rejects(()->TruckHidePolicy.shouldClick(false,true));rejects(()->TruckHidePolicy.shouldClick(true,false));
  check(TruckHidePolicy.ready(true,Boolean.TRUE,true,true));check(TruckHidePolicy.ready(true,Boolean.TRUE,false,false));check(TruckHidePolicy.ready(true,Boolean.TRUE,true,false));
  check(!TruckHidePolicy.ready(false,Boolean.FALSE,false,true));check(!TruckHidePolicy.ready(false,Boolean.FALSE,true,false));check(TruckHidePolicy.ready(false,Boolean.FALSE,true,true));
  check(!TruckHidePolicy.ready(true,Boolean.FALSE,true,true));check(!TruckHidePolicy.ready(false,Boolean.TRUE,true,true));check(!TruckHidePolicy.ready(true,null,true,true));check(!TruckHidePolicy.ready(false,null,false,false));
  System.out.println("Passed "+checks+" mandatory truck filter checks");}
}
