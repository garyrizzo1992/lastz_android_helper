package dev.codex.lastzhelper;
/** Calibrated against this build's even/odd row world-point records. */
final class WorldCoordinates {
 static int y(double worldZ){return (int)Math.round((-worldZ-1.1547)/1.73205);}
 static int x(double worldX,double worldZ){int row=y(worldZ);return (int)Math.round((worldX-1-(row&1))/2);}
}
