package dev.codex.lastzhelper;
public final class DeadStatePolicyTests {
 static int checks;static void check(boolean value){checks++;if(!value)throw new AssertionError("Dead state policy case"+checks);}
 static void rejects(Runnable action){boolean failed=false;try{action.run();}catch(IllegalArgumentException expected){failed=true;}check(failed);}
 public static void main(String[] args){
  check(DeadStatePolicy.permanent("The State you are searching for does not exist."));
  check(DeadStatePolicy.permanent(" <color=red>The State you are searching for does not exist.</color> "));
  check(DeadStatePolicy.permanent("THE STATE YOU ARE\n SEARCHING FOR DOES NOT EXIST."));
  check(!DeadStatePolicy.permanent("This server is unavailable"));check(!DeadStatePolicy.permanent("State 22 is not yet open."));
  check(!DeadStatePolicy.permanent("State/coordinate change not confirmed"));check(!DeadStatePolicy.permanent("Network connection failed"));
  check(!DeadStatePolicy.permanent("Player says The State you are searching for does not exist."));check(!DeadStatePolicy.permanent(""));
  check(DeadStatePolicy.state(1)==1&&DeadStatePolicy.state(9999)==9999);rejects(()->DeadStatePolicy.state(0));rejects(()->DeadStatePolicy.state(10000));
  System.out.println("Passed "+checks+" permanent dead-state policy checks");
 }
}
