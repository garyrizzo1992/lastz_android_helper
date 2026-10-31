package dev.codex.lastzhelper;

/** Pure conservative coverage/eligibility contracts; never loads device state. */
public final class MailCoverageTests {
 static int checks;
 static void expect(boolean value,String reason){if(!value)throw new AssertionError(reason);checks++;}
 interface Check{void run();}
 static void rejects(Check action){boolean rejected=false;try{action.run();}catch(IllegalArgumentException e){rejected=true;}expect(rejected,"Invalid observation rejected");}
 static final String UID="2059765822000064",ID="1430459303373848681";
 static MailCoveragePolicy.Attachment attachment(String recipient,boolean reward,long state,long deal,long expires){return MailCoveragePolicy.attachment(ID,recipient,UID,reward,state,deal,expires,100);}
 public static void main(String[] args){
  expect(MailCoveragePolicy.coverage(false,true,true,0,false,0)==MailCoveragePolicy.Coverage.UNINSPECTED,"closed/unloaded mailbox is not empty complete");
  expect(MailCoveragePolicy.coverage(true,true,true,0,false,0)==MailCoveragePolicy.Coverage.UNINSPECTED,"empty cache and absent paging flags remain uninspected");
  expect(MailCoveragePolicy.coverage(true,true,true,20,false,0)==MailCoveragePolicy.Coverage.PARTIAL,"cached headers alone are partial");
  expect(MailCoveragePolicy.coverage(true,true,true,0,true,0)==MailCoveragePolicy.Coverage.PARTIAL,"observed local paging flags do not prove empty server scope");
  expect(MailCoveragePolicy.coverage(true,true,true,20,true,1)==MailCoveragePolicy.Coverage.PENDING_METADATA_OBSERVED,"request metadata is reported without claiming active request semantics");
  expect(MailCoveragePolicy.coverage(true,false,true,20,true,0)==MailCoveragePolicy.Coverage.BLOCKED,"changed snapshot blocks coverage conclusions");
  expect(MailCoveragePolicy.coverage(true,true,false,20,true,0)==MailCoveragePolicy.Coverage.BLOCKED,"invalid/truncated fields block conclusions");
  expect(!MailCoveragePolicy.completeMailboxProven(),"no combination of local observations authorizes complete mailbox claim");
  rejects(()->MailCoveragePolicy.coverage(true,true,true,-1,true,0));rejects(()->MailCoveragePolicy.coverage(true,true,true,0,true,-1));
  expect(attachment(UID,true,0,0,101)==MailCoveragePolicy.Attachment.ORDINARY_CANDIDATE,"known own unexpired ordinary attachment is inspection candidate");
  expect(attachment(UID,true,0,100,101)==MailCoveragePolicy.Attachment.SPECIAL_PENDING,"deal100 announcement is excluded from ordinary claims");
  expect(attachment(UID,true,0,1,101)==MailCoveragePolicy.Attachment.SPECIAL_PENDING,"other nonzero deal cannot become ordinary");
  expect(attachment(UID,true,1,0,101)==MailCoveragePolicy.Attachment.ALREADY_RECEIVED,"received attachment not repeated");
  expect(attachment(UID,false,0,0,101)==MailCoveragePolicy.Attachment.NO_REWARD,"plain mail is not reward candidate");
  expect(attachment(UID,true,0,0,100)==MailCoveragePolicy.Attachment.EXPIRED,"expiry boundary excludes claim");
  expect(attachment(UID,true,0,0,0)==MailCoveragePolicy.Attachment.BLOCKED,"missing/permanent expiry semantics remain unknown");
  expect(attachment("other",true,0,0,101)==MailCoveragePolicy.Attachment.BLOCKED,"wrong recipient blocked");
  expect(attachment(UID,true,2,0,101)==MailCoveragePolicy.Attachment.BLOCKED,"unknown reward status blocked");
  expect(attachment(UID,true,0,-1,101)==MailCoveragePolicy.Attachment.BLOCKED,"unknown deal state blocked");
  expect(MailCoveragePolicy.attachment("00000000-0000-3-0000-000000000000",UID,UID,true,0,0,101,100)==MailCoveragePolicy.Attachment.BLOCKED,"synthetic-looking reward never ordinary");
  expect(MailCoveragePolicy.sameIdentity(UID,"123",5,1,UID,"123",5,1),"matching UID/process/tab accepted");
  expect(!MailCoveragePolicy.sameIdentity(UID,"123",5,1,"1430578113000153","123",5,1),"account change rejected");
  expect(!MailCoveragePolicy.sameIdentity(UID,"123",5,1,UID,"124",5,1),"process restart rejected");
  expect(!MailCoveragePolicy.sameIdentity(UID,"123",5,1,UID,"123",6,1),"PID change rejected");
  expect(!MailCoveragePolicy.sameIdentity(UID,"123",5,1,UID,"123",5,2),"selected group change rejected");
  expect(MailCoverageReader.keyMatches("#1","INTEGER",1),"exact integer group key observed");
  expect(MailCoverageReader.keyMatches("#1","ARRAY_INTEGER",1),"array group key retains integer type");
  expect(MailCoverageReader.keyMatches("1","STRING",1),"string group key explicitly retained");
  expect(!MailCoverageReader.keyMatches("#1","STRING",1),"literal hash-prefixed string is not numeric group key");
  expect(!MailCoverageReader.keyMatches("#1.0","FLOAT",1),"floating key not silently coerced to integer group");
  expect(!MailCoverageReader.keyMatches("#2","INTEGER",1),"different selected group does not match");
  // The live System sample has six received, fourteen plain and one special announcement.
  int ordinary=0,special=0,received=0,plain=0;
  for(int index=0;index<21;index++){
   boolean hasReward=index<6||index==20;long rewardState=index<6?1:0,deal=index==20?100:0;
   MailCoveragePolicy.Attachment decision=MailCoveragePolicy.attachment(Long.toString(1430459303373848681L+index),UID,UID,hasReward,rewardState,deal,1000,100);
   if(decision==MailCoveragePolicy.Attachment.ORDINARY_CANDIDATE)ordinary++;
   if(decision==MailCoveragePolicy.Attachment.SPECIAL_PENDING)special++;
   if(decision==MailCoveragePolicy.Attachment.ALREADY_RECEIVED)received++;
   if(decision==MailCoveragePolicy.Attachment.NO_REWARD)plain++;
  }
  expect(ordinary==0&&special==1&&received==6&&plain==14,"observed System mixture never promotes special announcement to ordinary reward");
  expect(MailCoveragePolicy.coverage(true,true,true,21,true,0)==MailCoveragePolicy.Coverage.PARTIAL,"System cache with stable empty end/request maps remains partial");
  expect(MailCoveragePolicy.coverage(true,true,true,0,true,0)==MailCoveragePolicy.Coverage.PARTIAL,"empty loaded Recharge/Favorite cache does not prove no server rewards");
  expect(MailCoveragePolicy.coverage(true,false,true,21,true,2)==MailCoveragePolicy.Coverage.BLOCKED,"moving snapshot wins over observed request metadata");
  expect(MailCoveragePolicy.coverage(true,true,false,21,true,2)==MailCoveragePolicy.Coverage.BLOCKED,"unsupported map shape wins over observed request metadata");
  expect(MailCoveragePolicy.attachment(ID,"",UID,true,0,100,1000,100)==MailCoveragePolicy.Attachment.BLOCKED,"special deal cannot mask missing own-recipient identity");
  expect(MailCoveragePolicy.attachment(ID,UID,UID,true,0,0,Long.MAX_VALUE,Long.MAX_VALUE)==MailCoveragePolicy.Attachment.EXPIRED,"expiry comparison does not overflow at long boundary");
  expect(MailCoveragePolicy.attachment("01430459303373848681",UID,UID,true,0,0,1000,100)==MailCoveragePolicy.Attachment.BLOCKED,"noncanonical leading-zero identity is not silently normalized");
  expect(MailCoveragePolicy.attachment(ID,UID,"clone1",true,0,0,1000,100)==MailCoveragePolicy.Attachment.BLOCKED,"clone label is not an account UID");
  expect(!MailCoveragePolicy.sameIdentity(UID,"123",5,1,UID,"123",5,-1),"closed or missing selected Mail context cannot stay stable");
  MailCoverageInspectionFeature feature=new MailCoverageInspectionFeature();
  expect(!feature.requiresInstrumentation(),"coverage inspection is explicitly memory only");
  expect(!feature.permitsInput("ui-tap","UIManagerInstance/windows/UIMailNew4/View/_btnAllRead",true),"read-all/claim input denied");
  expect(!feature.permitsInput("ui-tap",MailPolicy.ENTRY,true),"navigation input denied");
  expect(!feature.permitsInput("ui-bounds",MailPolicy.VIEW,true),"feature grants no native action permission");
  System.out.println("Passed "+checks+" Mail coverage checks");
 }
}
