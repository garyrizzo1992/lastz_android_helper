package dev.codex.lastzhelper;
import android.content.Context;import android.os.PowerManager;
/** Time-bounded display lease. Does not wake or unlock a sleeping device. */
@SuppressWarnings("deprecation")
final class RunAwake implements AutoCloseable {
 final PowerManager.WakeLock lock;
 RunAwake(Context context,long timeoutMs){PowerManager manager=(PowerManager)context.getSystemService(Context.POWER_SERVICE);lock=manager.newWakeLock(PowerManager.SCREEN_DIM_WAKE_LOCK,"LastZHelper:automation");lock.setReferenceCounted(false);lock.acquire(timeoutMs);}
 void renew(long timeoutMs){lock.acquire(timeoutMs);}
 public void close(){try{if(lock.isHeld())lock.release();}catch(RuntimeException e){android.util.Log.w("LastZHelper","Wake lease release failed",e);}}
}
