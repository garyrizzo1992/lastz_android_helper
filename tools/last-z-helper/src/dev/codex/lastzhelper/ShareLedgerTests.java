package dev.codex.lastzhelper;
import java.io.*;import org.json.*;
/** Receipt destination regression: group bounty receipts must not be labelled World. */
public final class ShareLedgerTests {
 public static void main(String[] args)throws Exception{
  File file=new File("/data/local/tmp/lastz-ledger-test-"+java.util.UUID.randomUUID()+".json");int checks=0;
  try{ShareLedger ledger=new ShareLedger(file);for(String kind:new String[]{"group-bounty","group-truck","private-truck","bounty","truck"}){
    ledger.pending(kind,new JSONObject().put("kind",kind));ledger.verified(kind,123);JSONObject record=new ShareLedger(file).data.getJSONObject(kind);String expected=kind.startsWith("group-")?"groupSequence":kind.startsWith("private-")?"privateSequence":"worldSequence";
    if(record.getLong(expected)!=123||!record.getString("status").equals("verified")||kind.startsWith("group-")&&record.has("worldSequence"))throw new AssertionError("Receipt destination "+kind);checks++;
   }System.out.println("Passed "+checks+" share-ledger destination checks");
  }finally{new File(file.getPath()+".tmp").delete();file.delete();}
 }
}
