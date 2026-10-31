package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"time"
)

func findRoot() (string, error) {
	var starts []string
	if cwd, e := os.Getwd(); e == nil {
		starts = append(starts, cwd)
	}
	if exe, e := os.Executable(); e == nil {
		starts = append(starts, filepath.Dir(exe))
	}
	for _, start := range starts {
		for path := start; ; path = filepath.Dir(path) {
			if _, err := os.Stat(filepath.Join(path, "config", "truck_scanner.json")); err == nil {
				return path, nil
			}
			if filepath.Dir(path) == path {
				break
			}
		}
	}
	return "", fmt.Errorf("could not locate LastZ config; run inside the repository")
}
func main() {
	if err := runMain(); err != nil {
		log.Print("ERROR: ", err)
		os.Exit(1)
	}
}
func runMain() error {
	root, err := findRoot()
	if err != nil {
		return err
	}
	adb := flag.String("adb", filepath.Join(root, "scrcpy", "adb.exe"), "ADB executable")
	serial := flag.String("serial", "", "Expected local USB serial")
	config := flag.String("config", filepath.Join(root, "config", "truck_scanner.json"), "Calibration JSON")
	output := flag.String("output", filepath.Join(root, "runtime", "truck-scanner", "go-"+time.Now().Format("20060102-150405")), "Evidence directory")
	state := flag.String("share-state", filepath.Join(root, "runtime", "truck-scanner", "world-shares.json"), "Durable World-sharing ledger")
	tesseractDefault, _ := exec.LookPath("tesseract")
	if tesseractDefault == "" {
		tesseractDefault = `C:\Program Files\Tesseract-OCR\tesseract.exe`
	}
	tesseract := flag.String("tesseract", tesseractDefault, "Tesseract executable (no Python required)")
	maxRefreshes := flag.Int("max-refreshes", -1, "Refresh cap; default -1 searches until found")
	until := flag.Bool("until-found", false, "Search until found (default)")
	current := flag.Bool("inspect-current", false, "Process the open truck, including any configured World share")
	capture := flag.Bool("capture", false, "Capture only; no taps")
	sound := flag.Bool("test-sound", false, "Test Windows alert only")
	flag.Parse()
	if *sound {
		return alertSound()
	}
	if *maxRefreshes < -1 {
		return fmt.Errorf("max-refreshes must be -1 or non-negative")
	}
	if *until && *maxRefreshes >= 0 {
		return fmt.Errorf("choose either until-found or max-refreshes")
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()
	phone, err := connect(ctx, *adb, *serial)
	if err != nil {
		return err
	}
	s, err := loadScanner(ctx, phone, *config, *output, *state, *tesseract)
	if err != nil {
		return err
	}
	if *capture {
		f, err := s.frame()
		if err != nil {
			return err
		}
		path, err := s.evidence("capture", f)
		log.Print("Screenshot: ", path)
		return err
	}
	log.Printf("Go scanner on USB %s; exactly two fragments -> World (any power); %d+ and power >=%d -> World; %d+ and power <%d -> sound/stop; never attacks", phone.Serial, s.Config.MinFragments, s.Config.MaxPower, s.Config.MinFragments, s.Config.MaxPower)
	return s.run(*maxRefreshes, *current)
}
