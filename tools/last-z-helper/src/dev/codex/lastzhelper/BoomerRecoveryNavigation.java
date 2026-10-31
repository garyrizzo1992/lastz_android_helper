package dev.codex.lastzhelper;
/** Rotation receipt adapter. Scope remains restricted through navigation cleanup. */
final class BoomerRecoveryNavigation {
 static int inspect(MaintenanceContext c)throws Exception{
  c.active();if(!c.store.unresolved(c.uid,BoomerReceiptRecovery.ID))return 0;
  if(c.activeFeature!=null)throw new IllegalStateException("Receipt recovery cannot overlap a feature");
  BoomerNavigator navigator=new BoomerNavigator(c);c.activeFeature=new BoomerReceiptNavigation();
  try{
   navigator.open();
   return BoomerReceiptRecovery.inspect(c.store,c.uid,c.preview,new BoomerReceiptRecovery.World(){
    public void active()throws Exception{c.active();}public long now(){return System.currentTimeMillis();}
    public org.json.JSONObject read()throws Exception{return new BoomerReader(c).read();}
   });
  }finally{try{c.active();navigator.close();}finally{c.activeFeature=null;}}
 }
}
