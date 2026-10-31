package dev.codex.lastzhelper;

/** Pure header-identity fixtures; does not infer status semantics or read a phone. */
public final class MailHeaderProbeTests {
 private static int checks;
 private static final String SELF="2059765822000064";
 private static void expect(MailHeaderProbePolicy.Identity expected,String id,String recipient,String uid,long type,boolean reward,long status,long deal){
  if(MailHeaderProbePolicy.identity(id,recipient,uid,type,reward,status,deal)!=expected)throw new AssertionError("Unexpected header identity classification");checks++;
 }
 public static void main(String[] args){
  MailHeaderProbePolicy.Identity own=MailHeaderProbePolicy.Identity.OWN,blocked=MailHeaderProbePolicy.Identity.BLOCKED,placeholder=MailHeaderProbePolicy.Identity.SYNTHETIC_PLACEHOLDER;
  expect(own,"1430459261720215782",SELF,SELF,1,true,0,0);
  expect(own,"1430459261720215783",SELF,SELF,1,false,1,0);
  // Unknown raw enums are observable, not prematurely assigned claim/read meanings.
  expect(own,"1",SELF,SELF,999,true,Long.MAX_VALUE,-1);
  expect(own,"99999999999999999999",SELF,SELF,1,false,0,0);
  for(String invalid:new String[]{null,"","0","01","-1","1.0","1e3","100000000000000000000","not-a-mail-id"})expect(blocked,invalid,SELF,SELF,1,false,1,0);
  expect(blocked,"1","another-recipient",SELF,1,false,1,0);
  expect(blocked,"1",null,SELF,1,false,1,0);
  expect(blocked,"1",SELF,null,1,false,1,0);
  expect(blocked,"1",SELF,"not-a-character",1,false,1,0);
  String[] synthetic={"00000000-0000-1-0000-000000000000","00000000-0000-2-0000-000000000000","00000000-0000-3-0000-000000000000"};long[] types={73,997,1000};
  for(int index=0;index<synthetic.length;index++){
   expect(placeholder,synthetic[index],"",SELF,types[index],false,1,0);
   expect(blocked,synthetic[index],"",SELF,types[index],true,1,0);
   expect(blocked,synthetic[index],"",SELF,types[index],false,0,0);
   expect(blocked,synthetic[index],"",SELF,types[index],false,1,100);
   expect(blocked,synthetic[index],SELF,SELF,types[index],false,1,0);
   expect(blocked,synthetic[index],"",SELF,types[index]+1,false,1,0);
  }
  expect(blocked,"00000000-0000-4-0000-000000000000","",SELF,1000,false,1,0);
  System.out.println("Passed "+checks+" Mail header probe checks");
 }
}
