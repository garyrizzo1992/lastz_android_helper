package dev.codex.lastzhelper;
/** Rotation receipt adapter. Scope remains restricted through navigation cleanup. */
final class BoomerRecoveryNavigation {
 static int inspect(MaintenanceContext c)throws Exception{
  BoomerNavigator navigator=new BoomerNavigator(c);
  return BoomerReceiptRecovery.navigate(c.store,c.uid,c.preview,new BoomerReceiptRecovery.Navigation(){
    public void enter(){if(c.activeFeature!=null)throw new IllegalStateException("Receipt recovery cannot overlap a feature");c.activeFeature=new BoomerReceiptNavigation();}
    public void leave(){c.activeFeature=null;}
    public void open()throws Exception{navigator.open();}
    public void close()throws Exception{navigator.close();}
    public void active()throws Exception{c.active();}public long now(){return System.currentTimeMillis();}
    public org.json.JSONObject read()throws Exception{return new BoomerReader(c).read();}
   });
 }
}
