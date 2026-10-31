package dev.codex.lastzhelper;

/** Identity filtering only. Raw Mail status/reward enums are deliberately uninterpreted. */
final class MailHeaderProbePolicy {
 enum Identity { OWN, SYNTHETIC_PLACEHOLDER, BLOCKED }
 static Identity identity(String id,String recipient,String expectedUid,long type,boolean reward,long rewardStatus,long deal){
  if(id==null||recipient==null||expectedUid==null||!expectedUid.matches("[0-9]{8,24}"))return Identity.BLOCKED;
  if(MailPolicy.placeholder(id,recipient,type,reward,rewardStatus,deal))return Identity.SYNTHETIC_PLACEHOLDER;
  return id.matches("[1-9][0-9]{0,19}")&&recipient.equals(expectedUid)?Identity.OWN:Identity.BLOCKED;
 }
}
