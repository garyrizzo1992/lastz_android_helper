package dev.codex.lastzhelper;
public final class BaseBubblePolicyTests {
 static int checks;static void expect(boolean b){if(!b)throw new AssertionError("check "+checks);checks++;}
 public static void main(String[] args){
  expect(BaseBubblePolicy.identity("#1256861592750932149",1256861592750932149L,423000));
  expect(!BaseBubblePolicy.identity("#1256861592750932148",1256861592750932149L,423000));expect(!BaseBubblePolicy.identity("#1",1,0));expect(!BaseBubblePolicy.identity("#0",0,423000));
  for(String key:new String[]{"uuid","funcUuid","itemId","count","type","buildUuid","queueUuid"})expect(BaseBubblePolicy.parameter(key));
  for(String key:new String[]{"position","callback","name","text","model","itemId/other"})expect(!BaseBubblePolicy.parameter(key));
  expect(BaseBubblePolicy.boundedName("BuildBubble").equals("BuildBubble"));expect(BaseBubblePolicy.boundedName("chat text").isEmpty());expect(BaseBubblePolicy.boundedName(null).isEmpty());expect(BaseBubblePolicy.boundedName("a/b").isEmpty());
  for(int item:new int[]{411000,423000,424000,425000})expect(BaseBubblePolicy.sensitiveBuilding(item));expect(!BaseBubblePolicy.sensitiveBuilding(1));
  expect(BaseBubblePolicy.inventoryIdentity("200394","1254334526042161344","200394","1254334526042161344",11941929));
  expect(!BaseBubblePolicy.inventoryIdentity("200394","1254334526042161344","200394","1254334526042161345",11941929));
  expect(!BaseBubblePolicy.inventoryIdentity("200394","1254334526042161344","200395","1254334526042161344",11941929));
  expect(!BaseBubblePolicy.inventoryIdentity("107207;145;0","1","107207;145;0","1",1));
  expect(!BaseBubblePolicy.inventoryIdentity("200394","1","200394","1",-1));
  BaseResourceGeometryFeature preview=new BaseResourceGeometryFeature();expect(preview.permitsInput("base-resource-geometry-preview","",true));expect(!preview.permitsInput("base-resource-geometry-preview","",false));expect(!preview.permitsInput("ui-tap","",true));expect(!preview.permitsInput("training-collect","",true));expect(!preview.permitsInput("map-tap","",true));
  System.out.println("Passed "+checks+" base bubble policy checks");
 }
}
