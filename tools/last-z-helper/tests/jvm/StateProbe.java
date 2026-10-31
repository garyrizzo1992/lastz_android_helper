package dev.codex.lastzhelper;
import java.io.*;import java.nio.file.*;
/** JVM filesystem adapter; no game or Android access. */
final class StateProbe {static String text(String path)throws Exception{return new String(Files.readAllBytes(new File(path).toPath()),"UTF-8").trim();}}
