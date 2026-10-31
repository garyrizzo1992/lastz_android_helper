package main

import (
	"context"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"testing"
	"time"
)

func fixture(t *testing.T, name string) *Frame {
	t.Helper()
	f, err := os.Open(filepath.Join("..", "..", "tests", "fixtures", name))
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	img, err := png.Decode(f)
	if err != nil {
		t.Fatal(err)
	}
	return newFrame(img)
}
func calibrated(t *testing.T) *Scanner {
	t.Helper()
	s, err := loadScanner(context.Background(), nil, filepath.Join("..", "..", "config", "truck_scanner.json"), t.TempDir(), filepath.Join(t.TempDir(), "shared.json"), "tesseract")
	if err != nil {
		t.Fatal(err)
	}
	s.Sleep = func(time.Duration) error { return nil }
	return s
}
func TestPowerParsing(t *testing.T) {
	for text, want := range map[string]int64{"439,123,456": 439123456, "439123456": 439123456, "439.5M": 439500000, "66.99M": 66990000, "1.1B": 1100000000, "430K": 430000} {
		got, ok := parsePower(text)
		if !ok || got != want {
			t.Errorf("%s -> %d/%v, want %d", text, got, ok, want)
		}
	}
	for _, text := range []string{"439", "Power 439M", "439,12,456", "4O0M", "439M 20M", ""} {
		if _, ok := parsePower(text); ok {
			t.Errorf("accepted %q", text)
		}
	}
}
func TestSharingIgnoresPowerAndAlertDoesNot(t *testing.T) {
	c := Config{MinFragments: 3, MaxPower: 440000000, ShareTwo: true}
	for _, power := range []int64{0, 439999999, 440000000, 900000000} {
		if !worldTarget(Observation{Fragments: 2, Power: power}, c) {
			t.Fatal("two-icon World share gated by power")
		}
	}
	if !alertTarget(Observation{Fragments: 3, Power: 439999999}, c) {
		t.Fatal("valid alert rejected")
	}
	for _, o := range []Observation{{Fragments: 3, Power: 440000000}, {Fragments: 2, Power: 100000000}, {Fragments: 3, Power: 0}} {
		if alertTarget(o, c) {
			t.Fatal("unsafe alert accepted")
		}
	}
	if worldTarget(Observation{Fragments: 3}, c) {
		t.Fatal("three icons must not use two-icon sharing rule")
	}
}
func TestWorldButtonFollowsGlobeNotRow(t *testing.T) {
	for _, y := range []int{400, 650, 900} {
		h, err := worldButton([]Hit{{X: 140, Y: y}}, []Hit{{X: 580, Y: y - 120}, {X: 580, Y: y}, {X: 580, Y: y + 120}})
		if err != nil || h.Y != y {
			t.Fatalf("world row %d: %v %v", y, h, err)
		}
	}
	for _, icons := range [][]Hit{nil, {{X: 140, Y: 800}, {X: 140, Y: 950}}} {
		if _, err := worldButton(icons, []Hit{{X: 580, Y: 800}}); err == nil {
			t.Fatal("ambiguous/missing world icon accepted")
		}
	}
	if _, err := worldButton([]Hit{{X: 140, Y: 800}}, []Hit{{X: 580, Y: 800}, {X: 500, Y: 810}}); err == nil {
		t.Fatal("ambiguous associated buttons accepted")
	}
}
func TestRealTwoFragmentIcons(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_two_fragments.png")
	count, err := s.fragments(f)
	if err != nil || count != 2 {
		t.Fatalf("count %d, err %v", count, err)
	}
	points, err := s.candidates(f)
	if err != nil {
		t.Fatal(err)
	}
	if len(points) != 4 {
		t.Fatalf("want 4 purple/yellow trucks, got %+v", points)
	}
}
func TestRealWorldIconAndRepeatedButtons(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_world_share.png")
	if err := s.require(f, "share_title", s.all(f)); err != nil {
		t.Error(err)
	}
	world := s.hits(f, "world_icon", s.all(f))
	buttons := s.hits(f, "share_button", s.all(f))
	h, err := worldButton(world, buttons)
	if err != nil || abs(h.X-587) > 5 || abs(h.Y-831) > 5 {
		t.Fatalf("wrong World control: %+v, %v; icons %+v buttons %+v", h, err, world, buttons)
	}
}

func TestWorldMenuWaitsForTransitionWithoutRequiringTitle(t *testing.T) {
	s := calibrated(t)
	menu := fixture(t, "truck_world_share.png")
	draw.Draw(menu.Img, image.Rect(300, 365, 420, 425), image.NewUniform(color.Black), image.Point{}, draw.Src)
	menu = newFrame(menu.Img)
	blank := newFrame(image.NewNRGBA(menu.Img.Bounds()))
	p := &fakePhone{frames: []*Frame{blank, menu}}
	s.Phone = p
	s.ReadText = func(*Frame, string, int, string) (string, error) { return "World", nil }
	_, button, err := s.waitWorldMenu()
	if err != nil || abs(button.Y-831) > 5 {
		t.Fatalf("menu not recovered: %+v %v", button, err)
	}
	if len(p.taps) != 0 {
		t.Fatal("waiting for menu must not tap anything")
	}
}

func TestWorldMenuWrongLabelNeverTaps(t *testing.T) {
	s := calibrated(t)
	menu := fixture(t, "truck_world_share.png")
	p := &fakePhone{frames: []*Frame{menu}}
	s.Phone = p
	s.ReadText = func(*Frame, string, int, string) (string, error) { return "Alliance", nil }
	if _, _, err := s.waitWorldMenu(); err == nil {
		t.Fatal("non-World label accepted")
	}
	if len(p.taps) != 0 {
		t.Fatal("wrong channel must never be clicked")
	}
}

func TestShareCoordinatesNormalizeAndSeparateStates(t *testing.T) {
	for _, text := range []string{"#26 X:588 Y:322", "26X588Y322"} {
		id, err := parseShareCoordinates(text)
		if err != nil || id != "state-26-x-588-y-322" {
			t.Fatalf("%s %s %v", text, id, err)
		}
	}
	if _, err := parseShareCoordinates("no coordinates"); err == nil {
		t.Fatal("accepted unknown identity")
	}
}

type fakePhone struct {
	frames []*Frame
	taps   []Hit
	swipes int
}

func (p *fakePhone) Screenshot() (*Frame, error) {
	if len(p.frames) > 1 {
		f := p.frames[0]
		p.frames = p.frames[1:]
		return f, nil
	}
	return p.frames[0], nil
}
func (p *fakePhone) Tap(h Hit) error  { p.taps = append(p.taps, h); return nil }
func (p *fakePhone) Swipe(Rect) error { p.swipes++; return nil }
func TestTwoFragmentsDoNotReadPower(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_two_fragments.png")
	p := &fakePhone{frames: []*Frame{f}}
	s.Phone = p
	s.ReadPower = func(*Frame) (int64, error) { t.Fatal("power read for two-fragment share"); return 0, nil }
	o, err := s.inspect(f)
	if err != nil || o.Fragments != 2 || o.Power != 0 {
		t.Fatalf("%+v %v", o, err)
	}
	if len(p.taps) != 0 {
		t.Fatal("inspect must never tap Share/Plunder")
	}
}
func TestDurableShareLedger(t *testing.T) {
	path := filepath.Join(t.TempDir(), "world-shares.json")
	state := ShareState{Targets: map[string]ShareRecord{"truck": {State: "pending", AttemptedAt: time.Now()}}}
	if err := saveJSON(path, state); err != nil {
		t.Fatal(err)
	}
	state.Targets["truck"] = ShareRecord{State: "verified", AttemptedAt: time.Now()}
	if err := saveJSON(path, state); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil || len(data) == 0 {
		t.Fatal("ledger missing")
	}
}
func TestTemplateMatchDoesNotAcceptFlatImages(t *testing.T) {
	img := image.NewNRGBA(image.Rect(0, 0, 90, 90))
	for y := 0; y < 90; y++ {
		for x := 0; x < 90; x++ {
			img.SetNRGBA(x, y, color.NRGBA{R: 30, G: 60, B: 90, A: 255})
		}
	}
	f := newFrame(img)
	if hits := match(f, f, Rect{0, 0, 90, 90}, .9); len(hits) != 0 {
		t.Fatal("flat template accepted")
	}
}

func TestWorldConfirmationRequiresItsGlobeAndWorldLabel(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_world_confirmation.png")
	h, err := s.worldConfirmation(f)
	if err != nil || abs(h.X-213) > 4 || abs(h.Y-1014) > 4 {
		t.Fatalf("wrong confirmation %+v %v", h, err)
	}
	draw.Draw(f.Img, image.Rect(320, 660, 395, 739), image.NewUniform(color.Black), image.Point{}, draw.Src)
	if _, err = s.worldConfirmation(newFrame(f.Img)); err == nil {
		t.Fatal("missing World globe must not accept Share")
	}
}

func TestWorldChatReceiptNeedsPowerStateAndTwoIcons(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_world_receipt.png")
	s.ReadPower = func(*Frame) (int64, error) { return 900000000, nil }
	s.ReadText = func(*Frame, string, int, string) (string, error) { return "State 26 S Truck", nil }
	if err := s.findWorldCard(f, 900000000, "26", 2); err != nil {
		t.Fatal(err)
	}
	if err := s.findWorldCard(f, 288690000, "26", 2); err == nil {
		t.Fatal("accepted wrong power receipt")
	}
	if err := s.findWorldCard(f, 900000000, "27", 2); err == nil {
		t.Fatal("accepted wrong state receipt")
	}
}

func TestThreeFragmentCandidateStillRequiresMatchingPowerFrames(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_two_fragments.png")
	icon := s.Templates["yellow_fragment"]
	draw.Draw(f.Img, image.Rect(304, 1152, 304+icon.W, 1152+icon.H), icon.Img, image.Point{}, draw.Src)
	f = newFrame(f.Img)
	s.Phone = &fakePhone{frames: []*Frame{f}}
	calls := 0
	s.ReadPower = func(*Frame) (int64, error) {
		calls++
		if calls == 1 {
			return 439000000, nil
		}
		return 449000000, nil
	}
	if _, err := s.inspect(f); err == nil {
		t.Fatal("inconsistent power must not qualify")
	}
	if calls != 2 {
		t.Fatalf("want two power frames, got %d", calls)
	}
}

func TestMovingGreenCoordinatesDoNotChangeOwnerIdentity(t *testing.T) {
	f := newFrame(image.NewNRGBA(image.Rect(0, 0, 60, 30)))
	r := Rect{0, 0, 60, 30}
	draw.Draw(f.Img, f.Img.Bounds(), image.NewUniform(color.NRGBA{R: 200, G: 200, B: 200, A: 255}), image.Point{}, draw.Src)
	draw.Draw(f.Img, image.Rect(2, 2, 20, 20), image.NewUniform(color.Black), image.Point{}, draw.Src)
	a, _ := identity(newFrame(f.Img), r)
	draw.Draw(f.Img, image.Rect(30, 2, 50, 20), image.NewUniform(color.NRGBA{R: 105, G: 150, B: 50, A: 255}), image.Point{}, draw.Src)
	b, _ := identity(newFrame(f.Img), r)
	if a != b {
		t.Fatal("moving green coordinates changed black-text owner fingerprint")
	}
}

func TestIdentityToleratesSmallRenderingNoiseNotDifferentOwner(t *testing.T) {
	a := make([]byte, 1000)
	b := make([]byte, 1000)
	for i := 0; i < 4; i++ {
		b[i] = 255
	}
	if !sameIdentity(a, b) {
		t.Fatal("small anti-aliasing noise rejected")
	}
	for i := 0; i < 100; i++ {
		b[i] = 255
	}
	if sameIdentity(a, b) {
		t.Fatal("different identity accepted")
	}
	if sameIdentity(nil, nil) {
		t.Fatal("missing identities accepted")
	}
}

func TestHighPowerThreeFragmentsShareWithoutAlert(t *testing.T) {
	c := Config{MinFragments: 3, MaxPower: 440000000, ShareTwo: true, ShareHighPower: true}
	for _, power := range []int64{440000000, 522170000, 900000000} {
		o := Observation{Fragments: 3, Power: power}
		if !worldTarget(o, c) || alertTarget(o, c) {
			t.Fatalf("wrong high-power decision for %d", power)
		}
	}
	o := Observation{Fragments: 3, Power: 439999999}
	if worldTarget(o, c) || !alertTarget(o, c) {
		t.Fatal("under-limit truck must alert instead of share")
	}
	if worldTarget(Observation{Fragments: 3, Power: 0}, c) {
		t.Fatal("unknown power must not authorize a high-power share")
	}
	c.ShareHighPower = false
	if worldTarget(Observation{Fragments: 3, Power: 522170000}, c) {
		t.Fatal("high-power sharing cannot ignore its toggle")
	}
}

func TestActual522MThreeFragmentScreen(t *testing.T) {
	s := calibrated(t)
	f := fixture(t, "truck_three_high_power.png")
	s.Phone = &fakePhone{frames: []*Frame{f}}
	s.ReadPower = func(*Frame) (int64, error) { return 522170000, nil }
	o, err := s.inspect(f)
	if err != nil || o.Fragments != 3 || o.Power != 522170000 {
		t.Fatalf("wrong observation %+v %v", o, err)
	}
	if alertTarget(o, s.Config) || !worldTarget(o, s.Config) {
		t.Fatal("522.17M must share and continue, not alert/stop")
	}
}

func TestRealPowerOCR522Not922(t *testing.T) {
	exe, err := exec.LookPath("tesseract")
	if err != nil {
		t.Skip("Tesseract not installed")
	}
	f := fixture(t, "truck_three_high_power.png")
	s := calibrated(t)
	part, err := f.crop(s.Config.PowerROI)
	if err != nil {
		t.Fatal(err)
	}
	power, err := powerOCR(context.Background(), exe, part, 440000000)
	if err != nil || power != 522170000 {
		t.Fatalf("actual 522.17M misread as %d: %v", power, err)
	}
}

func transientFragmentFrames(t *testing.T) (*Frame, *Frame) {
	three := fixture(t, "truck_three_high_power.png")
	two := newFrame(three.Img)
	draw.Draw(two.Img, image.Rect(100, 1147, 180, 1229), image.NewUniform(color.Black), image.Point{}, draw.Src)
	return three, newFrame(two.Img)
}

func TestTransientFragmentDifferenceIsRechecked(t *testing.T) {
	s := calibrated(t)
	three, two := transientFragmentFrames(t)
	s.Phone = &fakePhone{frames: []*Frame{three, two, three, three, three}}
	s.ReadPower = func(*Frame) (int64, error) { return 522170000, nil }
	o, err := s.inspect(three)
	if err != nil || o.Fragments != 3 {
		t.Fatalf("transient reading was not recovered %+v %v", o, err)
	}
}

func TestPersistentlyUnstableFragmentsNeverReadPowerOrAct(t *testing.T) {
	s := calibrated(t)
	three, two := transientFragmentFrames(t)
	p := &fakePhone{frames: []*Frame{three, two, three, two, three}}
	s.Phone = p
	s.ReadPower = func(*Frame) (int64, error) {
		t.Fatal("unstable count must not proceed to power/actions")
		return 0, nil
	}
	if _, err := s.inspect(three); err == nil {
		t.Fatal("unstable icons accepted")
	}
	if len(p.taps) != 0 {
		t.Fatal("unstable icons must not tap actions")
	}
}

func TestLiveCurrentWorldChatReceipt(t *testing.T) {
	if os.Getenv("LASTZ_TRUCK_LIVE_EXPECTED_POWER") == "" {
		t.Skip("operator-only, read-only live phone check")
	}
	s := calibrated(t)
	s.Tesseract = `C:\Program Files\Tesseract-OCR\tesseract.exe`
	p, err := connect(context.Background(), filepath.Join("..", "..", "scrcpy", "adb.exe"), "")
	if err != nil {
		t.Fatal(err)
	}
	s.Phone = p
	f, err := s.frame()
	if err != nil {
		t.Fatal(err)
	}
	power, err := strconv.ParseInt(os.Getenv("LASTZ_TRUCK_LIVE_EXPECTED_POWER"), 10, 64)
	if err != nil {
		t.Fatal(err)
	}
	fragments := 2
	if value := os.Getenv("LASTZ_TRUCK_LIVE_EXPECTED_FRAGMENTS"); value != "" {
		fragments, err = strconv.Atoi(value)
		if err != nil {
			t.Fatal(err)
		}
	}
	if err = s.findWorldCard(f, power, os.Getenv("LASTZ_TRUCK_LIVE_EXPECTED_STATE"), fragments); err != nil {
		t.Fatal(err)
	}
}
