package dev.codex.lastzhelper;

/** Conservative inspection policy. Local paging flags never prove server completeness. */
final class MailCoveragePolicy {
 enum Coverage {UNINSPECTED,PARTIAL,PENDING_METADATA_OBSERVED,BLOCKED}
 enum Attachment {ORDINARY_CANDIDATE,SPECIAL_PENDING,ALREADY_RECEIVED,NO_REWARD,EXPIRED,BLOCKED}

 static Coverage coverage(boolean contextConfirmed,boolean stable,boolean observationsValid,long loadedHeaders,boolean pagingObserved,long requestEntries){
  if(loadedHeaders<0||requestEntries<0)throw new IllegalArgumentException("Negative Mail observation count");
  if(!contextConfirmed)return Coverage.UNINSPECTED;
  if(!stable||!observationsValid)return Coverage.BLOCKED;
  if(requestEntries>0)return Coverage.PENDING_METADATA_OBSERVED;
  return loadedHeaders>0||pagingObserved?Coverage.PARTIAL:Coverage.UNINSPECTED;
 }

 static Attachment attachment(String id,String recipient,String expectedUid,boolean hasReward,long rewardStatus,long deal,long expires,long now){
  if(id==null||!id.matches("[1-9][0-9]{0,19}")||recipient==null||expectedUid==null||!expectedUid.matches("[0-9]{8,24}")||!recipient.equals(expectedUid)||rewardStatus<0||deal<0||now<0)return Attachment.BLOCKED;
  if(!hasReward)return Attachment.NO_REWARD;
  if(rewardStatus==1)return Attachment.ALREADY_RECEIVED;
  if(rewardStatus!=0)return Attachment.BLOCKED;
  if(deal!=0)return Attachment.SPECIAL_PENDING;
  if(expires<=0)return Attachment.BLOCKED;
  return expires>now?Attachment.ORDINARY_CANDIDATE:Attachment.EXPIRED;
 }

 static boolean completeMailboxProven(){return false;}
 static boolean sameIdentity(String uid,String processStart,int pid,int tab,String afterUid,String afterStart,int afterPid,int afterTab){
  return uid!=null&&!uid.isEmpty()&&uid.equals(afterUid)&&processStart!=null&&!processStart.isEmpty()&&processStart.equals(afterStart)&&pid>0&&pid==afterPid&&tab>0&&tab==afterTab;
 }
}
