package dev.codex.lastzhelper;
/** Android JSON parser regression checks. No game state or input required. */
public final class ReceiptTests {
 static int passed;static void expect(boolean value){if(!value)throw new AssertionError("Receipt check "+(passed+1));passed++;}
 public static void main(String[] args)throws Exception{
  expect(ChatTileIdentity.attachment("{\"trainUuid\":1430458630091584086,\"postType\":604}",604).equals("1430458630091584086"));
  expect(ChatTileIdentity.attachment("{\"trainUuid\":1430458630091584087}",604).equals("1430458630091584087"));
  expect(ChatTileIdentity.attachment("{\"trainUuid\":\"1430458630091584086\"}",604).equals("1430458630091584086"));
  expect(ChatTileIdentity.attachment("{\"dispatchTaskUuid\":\"1430458630091584086\",\"postType\":630}",630).equals("1430458630091584086"));
  expect(ChatTileIdentity.attachment("{\"dispatchTaskUuid\":1430458630091584087}",630).equals("1430458630091584087"));
  boolean rejected=false;try{ChatTileIdentity.attachment("{\"trainUuid\":1430458630091584086,\"postType\":630}",604);}catch(Exception e){rejected=true;}expect(rejected);
  rejected=false;try{ChatTileIdentity.attachment("{\"trainUuid\":1}",630);}catch(Exception e){rejected=true;}expect(rejected);
  rejected=false;try{ChatTileIdentity.attachment("{}",0);}catch(Exception e){rejected=true;}expect(rejected);
  rejected=false;try{ChatTileIdentity.attachment("{\"trainUuid\":1.430458630091584E18}",604);}catch(Exception e){rejected=true;}expect(rejected);
  rejected=false;try{ChatTileIdentity.attachment("{\"trainUuid\":\"9223372036854775808\"}",604);}catch(Exception e){rejected=true;}expect(rejected);
  System.out.println("Passed "+passed+" Android receipt tests");
  if(args.length==1)try(GameMemory m=new GameMemory(args[0])){
   long rooms=m.path("ChatManager2/Instance/Room");String room=GameMemory.string(rooms,"countryRoomId");long messages=GameMemory.f(GameMemory.f(GameMemory.f(rooms,"roomDatas"),room),"msgs");
   long truck=0,bounty=0,truckSeq=0,bountySeq=0;
   for(TruckDiscoveryProbe.Value v:GameMemory.rows(messages))if((v.tag&15)==5){long post=GameMemory.number(v.raw,"post"),seq=GameMemory.number(v.raw,"seqId");if(post==604&&seq>truckSeq){truck=v.raw;truckSeq=seq;}if(post==630&&seq>bountySeq){bounty=v.raw;bountySeq=seq;}}
   if(truck!=0)System.out.println("Live World truck receipt: sequence="+truckSeq+", UUID="+ChatTileIdentity.read(truck,604));
   if(bounty!=0)System.out.println("Live World bounty receipt: sequence="+bountySeq+", UUID="+ChatTileIdentity.read(bounty,630));
  }
 }
}
