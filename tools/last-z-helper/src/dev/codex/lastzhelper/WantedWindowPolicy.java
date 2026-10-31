package dev.codex.lastzhelper;
/** Only the observed, nonmodal game message banner is a passive Wanted overlay. */
final class WantedWindowPolicy {
 static boolean passiveNotice(String name,String prefab,boolean inModalStack){
  return !inModalStack&&"UICommonMessageBar".equals(name)&&"Assets/Main/Prefabs/UI/Common/UICommonMessageBar.prefab".equals(prefab);
 }
}
