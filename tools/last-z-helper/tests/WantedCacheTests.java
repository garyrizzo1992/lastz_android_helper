package dev.codex.lastzhelper;

import java.util.*;

/** Pure hidden-shortcut policy fixtures; no game, JSON or Android dependency. */
public final class WantedCacheTests {
 private static int checks;
 private static void expect(WantedCachePolicy.Decision expected,boolean hidden,boolean loaded,List<String> decisions){
  WantedCachePolicy.Decision actual=WantedCachePolicy.classify(hidden,loaded,decisions);
  if(actual!=expected)throw new AssertionError("Expected "+expected+", got "+actual+" for hidden="+hidden+", loaded="+loaded+", decisions="+decisions);
  checks++;
 }
 public static void main(String[] args){
  WantedCachePolicy.Decision visible=WantedCachePolicy.Decision.VISIBLE,blocked=WantedCachePolicy.Decision.BLOCKED,noReady=WantedCachePolicy.Decision.NO_READY_IN_LOADED_CACHE;

  // An active shortcut belongs to the normal inspection flow, never cache no-work.
  expect(visible,false,false,null);
  expect(visible,false,true,Collections.emptyList());
  expect(visible,false,true,Arrays.asList("READY_INSPECTION_ONLY"));

  // Hiding and an empty/unloaded cache cannot establish anything about the server.
  expect(blocked,true,false,Arrays.asList("ALREADY_RECEIVED"));
  expect(blocked,true,false,Arrays.asList("WAITING"));
  expect(blocked,true,true,null);
  expect(blocked,true,true,Collections.emptyList());
  expect(noReady,true,true,Collections.singletonList("ALREADY_RECEIVED"));
  expect(noReady,true,true,Collections.singletonList("WAITING"));
  expect(noReady,true,true,Arrays.asList("ALREADY_RECEIVED","WAITING","ALREADY_RECEIVED"));

  // A single uncertain, eligible or excluded record invalidates the no-ready claim.
  for(String unsupported:new String[]{"READY_INSPECTION_ONLY","BLOCKED","EXCLUDED","NOTHING_TO_DO","",null,"WAITING ","waiting"}){
   expect(blocked,true,true,Collections.singletonList(unsupported));
   expect(blocked,true,true,Arrays.asList("ALREADY_RECEIVED",unsupported,"WAITING"));
  }

  List<String> maximum=new ArrayList<>(Collections.nCopies(64,"ALREADY_RECEIVED"));
  maximum.set(63,"WAITING");
  expect(noReady,true,true,Collections.unmodifiableList(maximum));
  List<String> overbound=new ArrayList<>(maximum);overbound.add("WAITING");
  expect(blocked,true,true,overbound);
  List<String> before=new ArrayList<>(maximum);
  WantedCachePolicy.classify(true,true,maximum);
  if(!before.equals(maximum))throw new AssertionError("Policy mutated caller decisions");
  checks++;
  System.out.println("Passed "+checks+" Wanted cache checks");
 }
}
