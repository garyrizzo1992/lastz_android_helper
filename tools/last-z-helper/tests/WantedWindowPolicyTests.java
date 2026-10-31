package dev.codex.lastzhelper;
public final class WantedWindowPolicyTests {
 static int checks;static void expect(boolean v,String m){if(!v)throw new AssertionError(m);checks++;}
 public static void main(String[] args){String prefab="Assets/Main/Prefabs/UI/Common/UICommonMessageBar.prefab";
  expect(WantedWindowPolicy.passiveNotice("UICommonMessageBar",prefab,false),"observed nonmodal banner");
  expect(!WantedWindowPolicy.passiveNotice("UICommonMessageBar",prefab,true),"modal banner must block");
  for(String name:new String[]{"UIUnknown","UICommonMessageBar2","UIDispatchRewardGet","",null})expect(!WantedWindowPolicy.passiveNotice(name,prefab,false),"unknown/reward window stays guarded");
  for(String path:new String[]{"Assets/Other/UICommonMessageBar.prefab","",null})expect(!WantedWindowPolicy.passiveNotice("UICommonMessageBar",path,false),"changed or missing prefab blocks");
  System.out.println("Wanted passive window: "+checks+" checks passed");
 }
}
