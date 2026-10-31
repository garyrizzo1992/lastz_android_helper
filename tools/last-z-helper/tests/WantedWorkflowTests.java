package dev.codex.lastzhelper;

/** JVM-only capability and eligibility regressions. Never connects to a game. */
public final class WantedWorkflowTests {
 private static int checks;
 private static void expect(boolean condition,String message){
  if(!condition)throw new AssertionError(message);
  checks++;
 }
 private static void decision(String expected,long uuid,long rewarded,long start,long end,long now,boolean steal,String owner,long point){
  expect(expected.equals(WantedPolicy.classify(uuid,rewarded,start,end,now,steal,owner,point)),"Unexpected classification: "+expected);
 }
 public static void main(String[] args){
  WantedFeature workflow=new WantedFeature();
  WantedClaimCheckFeature claim=new WantedClaimCheckFeature();
  String receive=WantedPolicy.PANEL+"/cellList/#1/receive_btn";

  // Preview can navigate into and out of the inspected panel, but cannot consume.
  expect(workflow.permitsInput("ui-tap",WantedFeature.ENTRY,true),"Preview must permit the Wanted entry");
  expect(workflow.permitsInput("ui-tap",WantedFeature.CLOSE,true),"Preview must permit panel cleanup");
  expect(workflow.permitsInput("ui-tap","UIManagerInstance/windows/MainUI_SU/View/bottomLayer/home_btn",true),"Preview must permit the normal base-navigation control");
  expect(!workflow.permitsInput("ui-tap",receive,true),"Preview must never claim");
  expect(!workflow.permitsInput("ui-tap",WantedFeature.REWARD,true),"Preview cannot dismiss an unowned reward overlay");
  expect(!claim.permitsInput("ui-tap",receive,true),"Diagnostic preview must never claim");

  // Live capabilities are exact, bounded paths, never generic taps or mission starts.
  expect(workflow.permitsInput("ui-tap",receive,false),"Live workflow permits a guarded Receive button");
  expect(workflow.permitsInput("ui-tap",WantedFeature.REWARD,false),"Live workflow permits its reward cleanup control");
  expect(claim.permitsInput("ui-tap",WantedPolicy.PANEL+"/cellList/#99/receive_btn",false),"Supported row bound accepts its upper index");
  String[] forbidden={
   WantedPolicy.PANEL+"/cellList/#0/receive_btn",
   WantedPolicy.PANEL+"/cellList/#01/receive_btn",
   WantedPolicy.PANEL+"/cellList/#100/receive_btn",
   WantedPolicy.PANEL+"/cellList/#-1/receive_btn",
   WantedPolicy.PANEL+"/cellList/#+1/receive_btn",
   WantedPolicy.PANEL+"/cellList/#1.0/receive_btn",
   WantedPolicy.PANEL+"/cellList/#1/go_btn",
   WantedPolicy.PANEL+"/cellList/#1/receive_btn_txt",
   WantedPolicy.PANEL+"/cellList/#1/receive_btn/child",
   WantedPolicy.PANEL+"/refresh_btn",
   WantedPolicy.PANEL+"/allRefreshBtn",
   WantedPolicy.PANEL+"/star_btn",
   WantedPolicy.VIEW+"panelComponentList/400002/cellList/#1/receive_btn",
   "prefix/"+receive,
   receive+"/../go_btn"
  };
  for(String path:forbidden){
   expect(!claim.permitsInput("ui-tap",path,false),"Claim diagnostic accepted forbidden path "+path);
   expect(!workflow.permitsInput("ui-tap",path,false),"Production workflow accepted forbidden path "+path);
  }
  for(String action:new String[]{"map-tap","ui-swipe","back","text","clipboard"}){
   expect(!workflow.permitsInput(action,receive,false),"Production workflow accepted unrelated input "+action);
   expect(!claim.permitsInput(action,receive,false),"Claim diagnostic accepted unrelated input "+action);
  }

  // Timing boundaries distinguish a completed reward from a mission still running.
  decision("READY_INSPECTION_ONLY",1430459261720215782L,0,10,100,100,false,"",0);
  decision("WAITING",1430459261720215782L,0,10,101,100,false,"",0);
  decision("ALREADY_RECEIVED",1430459261720215782L,1,10,100,100,false,"",0);
  decision("BLOCKED",0,0,10,100,100,false,"",0);
  decision("BLOCKED",-1,0,10,100,100,false,"",0);
  decision("BLOCKED",1,-1,10,100,100,false,"",0);
  decision("BLOCKED",1,2,10,100,100,false,"",0);
  decision("BLOCKED",1,0,0,100,100,false,"",0);
  decision("BLOCKED",1,0,100,100,100,false,"",0);
  decision("BLOCKED",1,0,101,100,100,false,"",0);
  decision("BLOCKED",1,0,10,100,0,false,"",0);
  decision("BLOCKED",1,0,10,100,-1,false,"",0);
  decision("BLOCKED",1,0,101,102,100,false,"",0);
  decision("BLOCKED",1,1,101,102,100,false,"",0);
  decision("BLOCKED",1,0,-1,100,100,false,"",0);
  decision("BLOCKED",1,0,10,Long.MIN_VALUE,100,false,"",0);
  // Exact 19-digit task identities must remain valid without a floating conversion.
  decision("READY_INSPECTION_ONLY",1430459261720215783L,0,10,100,100,false,"",0);
  // Large timestamps remain ordered without subtraction/multiplication overflow.
  decision("WAITING",1,0,10,Long.MAX_VALUE,100,false,"",0);
  decision("READY_INSPECTION_ONLY",1,0,10,Long.MAX_VALUE,Long.MAX_VALUE,false,"",0);
  // A claimed task with corrupt timer metadata still cannot conceal malformed data.
  decision("BLOCKED",1,1,0,100,100,false,"",0);

  // Other-owner, world and stealing records remain excluded even if their timer ended.
  decision("EXCLUDED",1,0,10,100,100,true,"",0);
  decision("EXCLUDED",1,0,10,100,100,false,"another-player",0);
  decision("EXCLUDED",1,0,10,100,100,false," ",0);
  decision("EXCLUDED",1,0,10,100,100,false,null,0);
  decision("EXCLUDED",1,0,10,100,100,false,"",1);
  decision("EXCLUDED",1,0,10,100,100,false,"",-1);
  decision("EXCLUDED",0,0,0,0,100,true,"",0);
  System.out.println("Passed "+checks+" Wanted workflow checks");
 }
}
