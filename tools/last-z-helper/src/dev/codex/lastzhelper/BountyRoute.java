package dev.codex.lastzhelper;
/** Destination-specific identity preserves existing World history and checkpoints. */
final class BountyRoute {
 static final String WORLD="bounties",GROUP="bounties-group";
 static boolean known(String mode){return WORLD.equals(mode)||GROUP.equals(mode);}
 static String key(boolean group,String room,String id){return group?"group-bounty:"+room+":"+id:"bounty:"+id;}
 static String checkpoint(boolean group,boolean dry){return "bounty-"+(group?"group-progress":"progress")+(dry?"-dry":"")+".json";}
}
