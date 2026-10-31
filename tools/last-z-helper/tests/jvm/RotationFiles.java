package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;import org.json.*;
/** Filesystem adapter for testing production state classes off-device. */
final class RotationFiles {static void write(File file,JSONObject value)throws Exception{File tmp=new File(file+".tmp");try(FileOutputStream out=new FileOutputStream(tmp)){out.write(value.toString(2).getBytes("UTF-8"));out.getFD().sync();}Files.move(tmp.toPath(),file.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}}
