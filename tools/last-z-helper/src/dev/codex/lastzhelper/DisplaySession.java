package dev.codex.lastzhelper;
/** Runs use the existing game surface. Never resize, relaunch, or focus another task. */
final class DisplaySession implements AutoCloseable {
 DisplaySession()throws Exception{StateProbe.pinForeground();}
 public void close()throws Exception{DeviceInput.closeActive();}
}
