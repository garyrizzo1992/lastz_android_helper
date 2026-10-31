package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"image/png"
	"log"
	"math/bits"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type Config struct {
	Calibrated       bool              `json:"calibrated"`
	Resolution       [2]int            `json:"resolution"`
	MaxPower         int64             `json:"max_power"`
	MinFragments     int               `json:"min_fragments"`
	Threshold        float64           `json:"match_threshold"`
	Settle           float64           `json:"settle_seconds"`
	VerifyDelay      float64           `json:"verification_delay"`
	Templates        map[string]string `json:"templates"`
	TruckROI         Rect              `json:"truck_list_roi"`
	ListROI          Rect              `json:"list_marker_roi"`
	DetailROI        Rect              `json:"detail_marker_roi"`
	PowerROI         Rect              `json:"power_roi"`
	CargoROI         Rect              `json:"cargo_roi"`
	ResetSwipe       Rect              `json:"cargo_reset_swipe"`
	RefreshROI       Rect              `json:"refresh_roi"`
	FreeRefresh      bool              `json:"observed_free_refresh"`
	ShareEntryROI    Rect              `json:"share_entry_roi"`
	ShareIdentityROI Rect              `json:"share_identity_roi"`
	TruckIdentityROI Rect              `json:"truck_identity_roi"`
	ChatOpenPoint    [2]int            `json:"chat_open_point"`
	ShareTwo         bool              `json:"share_two_fragments_world"`
	ShareHighPower   bool              `json:"share_high_power_fragments_world"`
	ShareInterval    float64           `json:"world_share_interval_seconds"`
}
type Device interface {
	Screenshot() (*Frame, error)
	Tap(Hit) error
	Swipe(Rect) error
}
type Candidate struct {
	Hit
	Grade string
}
type Observation struct {
	Fragments int
	Power     int64
	Frame     *Frame
}
type Scanner struct {
	Context                      context.Context
	Phone                        Device
	Config                       Config
	Templates                    map[string]*Frame
	Output, StatePath, Tesseract string
	ReadPower                    func(*Frame) (int64, error)
	ReadText                     func(*Frame, string, int, string) (string, error)
	ReceiptVerified              bool
	ListChanged                  bool
	Sleep                        func(time.Duration) error
	Alert                        func() error
}

func loadScanner(ctx context.Context, phone Device, configPath, output, state, tesseract string) (*Scanner, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}
	var cfg Config
	if err = json.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	if !cfg.Calibrated || cfg.Resolution[0] <= 0 || cfg.Resolution[1] <= 0 {
		return nil, fmt.Errorf("configuration not calibrated")
	}
	if cfg.Threshold < .8 || cfg.Threshold > 1 || cfg.MaxPower <= 0 || cfg.MinFragments < 3 || cfg.MinFragments > 5 {
		return nil, fmt.Errorf("invalid matching/target configuration")
	}
	if !cfg.FreeRefresh {
		return nil, fmt.Errorf("this layout's free Refresh has not been calibrated")
	}
	s := &Scanner{Context: ctx, Phone: phone, Config: cfg, Templates: map[string]*Frame{}, Output: output, StatePath: state, Tesseract: tesseract}
	s.Sleep = func(d time.Duration) error { return wait(ctx, d) }
	s.Alert = alertSound
	s.ReadPower = func(f *Frame) (int64, error) { return powerOCR(ctx, s.Tesseract, f, s.Config.MaxPower) }
	s.ReadText = func(f *Frame, psm string, scale int, whitelist string) (string, error) {
		return ocr(ctx, s.Tesseract, f, psm, scale, whitelist)
	}
	for _, name := range []string{"purple_truck", "yellow_truck", "purple_cab", "yellow_cab", "yellow_fragment", "list_marker", "detail_marker", "refresh", "share_entry", "world_icon", "share_button", "share_title", "share_close", "world_confirm_icon", "world_confirm_label", "world_confirm_share", "world_confirm_cancel", "truck_back", "chat_world_tab", "chat_world_selected", "chat_truck_header", "truck_entry", "chat_back", "chat_fragment"} {
		path, ok := cfg.Templates[name]
		if !ok {
			return nil, fmt.Errorf("missing template %s", name)
		}
		f, err := os.Open(filepath.Join(filepath.Dir(configPath), filepath.FromSlash(path)))
		if err != nil {
			return nil, err
		}
		img, e := png.Decode(f)
		f.Close()
		if e != nil {
			return nil, e
		}
		s.Templates[name] = newFrame(img)
	}
	for _, roi := range []Rect{cfg.TruckROI, cfg.ListROI, cfg.DetailROI, cfg.PowerROI, cfg.CargoROI, cfg.RefreshROI, cfg.ShareEntryROI, cfg.ShareIdentityROI} {
		if roi[0] < 0 || roi[1] < 0 || roi[2] <= roi[0] || roi[3] <= roi[1] || roi[2] > cfg.Resolution[0] || roi[3] > cfg.Resolution[1] {
			return nil, fmt.Errorf("invalid calibrated ROI %v", roi)
		}
	}
	return s, nil
}
func (s *Scanner) frame() (*Frame, error) {
	f, err := s.Phone.Screenshot()
	if err != nil {
		return nil, err
	}
	if f.W != s.Config.Resolution[0] || f.H != s.Config.Resolution[1] {
		return nil, fmt.Errorf("screen resolution differs from calibration")
	}
	return f, nil
}
func (s *Scanner) hits(f *Frame, name string, roi Rect) []Hit {
	return match(f, s.Templates[name], roi, s.Config.Threshold)
}
func unique(hits []Hit, name string) (Hit, error) {
	if len(hits) != 1 {
		return Hit{}, fmt.Errorf("expected one %s, found %d", name, len(hits))
	}
	return hits[0], nil
}
func (s *Scanner) require(f *Frame, name string, roi Rect) error {
	_, err := unique(s.hits(f, name, roi), name)
	return err
}
func (s *Scanner) all(f *Frame) Rect { return Rect{0, 0, f.W, f.H} }
func (s *Scanner) evidence(name string, f *Frame) (string, error) {
	if err := os.MkdirAll(s.Output, 0700); err != nil {
		return "", err
	}
	path := filepath.Join(s.Output, name+".png")
	file, err := os.Create(path)
	if err != nil {
		return "", err
	}
	err = png.Encode(file, f.Img)
	closeErr := file.Close()
	if err == nil {
		err = closeErr
	}
	return path, err
}
func (s *Scanner) fragments(f *Frame) (int, error) {
	if err := s.require(f, "detail_marker", s.Config.DetailROI); err != nil {
		return 0, err
	}
	return len(s.hits(f, "yellow_fragment", s.Config.CargoROI)), nil
}
func (s *Scanner) inspect(f *Frame) (Observation, error) {
	if err := s.require(f, "detail_marker", s.Config.DetailROI); err != nil {
		return Observation{}, err
	}
	stable := false
	for attempt := 0; attempt < 5; attempt++ {
		before := f
		if err := s.Phone.Swipe(s.Config.ResetSwipe); err != nil {
			return Observation{}, err
		}
		if err := s.Sleep(350 * time.Millisecond); err != nil {
			return Observation{}, err
		}
		var err error
		f, err = s.frame()
		if err != nil {
			return Observation{}, err
		}
		if err = s.require(f, "detail_marker", s.Config.DetailROI); err != nil {
			return Observation{}, err
		}
		if difference(before, f, s.Config.CargoROI) < 3 {
			stable = true
			break
		}
	}
	if !stable {
		return Observation{}, fmt.Errorf("cargo start could not be verified")
	}
	count, err := s.fragments(f)
	if err != nil {
		return Observation{}, err
	}
	after := f
	readings := []int{count}
	stable = false
	for attempt := 0; attempt < 4; attempt++ {
		if err = s.Sleep(time.Duration(s.Config.VerifyDelay * float64(time.Second))); err != nil {
			return Observation{}, err
		}
		after, err = s.frame()
		if err != nil {
			return Observation{}, err
		}
		other, e := s.fragments(after)
		if e != nil {
			return Observation{}, e
		}
		readings = append(readings, other)
		if other == count {
			stable = true
			break
		}
		count = other
		log.Printf("Fragment reading changed (%v); waiting for two consecutive matching frames", readings)
	}
	if !stable {
		_, _ = s.evidence("unstable-fragments", after)
		return Observation{}, fmt.Errorf("fragment count remained unstable after bounded retries: %v", readings)
	}
	result := Observation{Fragments: count, Frame: after}
	// Two-fragment World shares ignore power entirely, as requested.
	if count < s.Config.MinFragments {
		return result, nil
	}
	powerFrame, err := after.crop(s.Config.PowerROI)
	if err != nil {
		return result, err
	}
	p1, err := s.ReadPower(powerFrame)
	if err != nil {
		return result, err
	}
	if err = s.Sleep(time.Duration(s.Config.VerifyDelay * float64(time.Second))); err != nil {
		return result, err
	}
	next, err := s.frame()
	if err != nil {
		return result, err
	}
	nextCount, err := s.fragments(next)
	if err != nil {
		return result, err
	}
	powerFrame, err = next.crop(s.Config.PowerROI)
	if err != nil {
		return result, err
	}
	p2, err := s.ReadPower(powerFrame)
	if err != nil {
		return result, err
	}
	if p1 != p2 || nextCount != count {
		return result, fmt.Errorf("candidate power/cargo changed; no alert")
	}
	result.Power = p1
	result.Frame = next
	return result, nil
}
func (s *Scanner) candidates(f *Frame) ([]Candidate, error) {
	if err := s.require(f, "list_marker", s.Config.ListROI); err != nil {
		return nil, err
	}
	var out []Candidate
	for _, name := range []string{"yellow_truck", "purple_truck", "yellow_cab", "purple_cab"} {
		for _, h := range s.hits(f, name, s.Config.TruckROI) {
			purple := strings.HasPrefix(name, "purple")
			if gradeRatio(f, s.Templates[name], h, purple) < .4 {
				continue
			}
			if strings.HasSuffix(name, "_cab") {
				h.X -= 75
			}
			duplicate := false
			for _, p := range out {
				if abs(h.X-p.X) <= 65 && abs(h.Y-p.Y) <= 45 {
					duplicate = true
					break
				}
			}
			if !duplicate {
				grade := "yellow"
				if purple {
					grade = "purple"
				}
				out = append(out, Candidate{h, grade})
			}
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Y == out[j].Y {
			return out[i].X < out[j].X
		}
		return out[i].Y < out[j].Y
	})
	return out, nil
}
func alertTarget(o Observation, c Config) bool {
	return o.Fragments >= c.MinFragments && o.Power > 0 && o.Power < c.MaxPower
}
func worldTarget(o Observation, c Config) bool {
	return c.ShareTwo && o.Fragments == 2 || c.ShareHighPower && o.Fragments >= c.MinFragments && o.Power > 0 && o.Power >= c.MaxPower
}
func (s *Scanner) refresh(f *Frame) error {
	if err := s.require(f, "list_marker", s.Config.ListROI); err != nil {
		return err
	}
	button, err := unique(s.hits(f, "refresh", s.Config.RefreshROI), "Refresh")
	if err != nil {
		return err
	}
	if err = s.Phone.Tap(button); err != nil {
		return err
	}
	if err = s.Sleep(time.Duration(s.Config.Settle * float64(time.Second))); err != nil {
		return err
	}
	after, err := s.frame()
	if err != nil {
		return err
	}
	if err = s.require(after, "list_marker", s.Config.ListROI); err != nil {
		return err
	}
	if difference(f, after, s.Config.TruckROI) < 2 {
		return fmt.Errorf("list did not change after Refresh")
	}
	return nil
}
func (s *Scanner) handle(o Observation) (bool, error) {
	if _, err := s.evidence("last-truck", o.Frame); err != nil {
		return false, err
	}
	if alertTarget(o, s.Config) {
		path, err := s.evidence("MATCH", o.Frame)
		if err != nil {
			return false, err
		}
		if err = saveJSON(filepath.Join(s.Output, "match.json"), map[string]any{"fragments": o.Fragments, "power": o.Power, "screenshot": path, "found_at": time.Now()}); err != nil {
			return false, err
		}
		log.Printf("MATCH: %d Universal Orange Hero Fragment icons; power %d. Left open, no attack.", o.Fragments, o.Power)
		return true, s.Alert()
	}
	if worldTarget(o, s.Config) {
		return false, s.shareWorld(o)
	}
	return false, nil
}
func (s *Scanner) run(maxRefreshes int, inspectCurrent bool) error {
	if inspectCurrent {
		f, err := s.frame()
		if err != nil {
			return err
		}
		o, err := s.inspect(f)
		if err != nil {
			return err
		}
		log.Printf("Current truck: %d fragment icons, power %d (zero means not needed)", o.Fragments, o.Power)
		_, err = s.handle(o)
		return err
	}
	driftRetries := 0
	for round := 0; maxRefreshes < 0 || round <= maxRefreshes; round++ {
		f, err := s.frame()
		if err != nil {
			return err
		}
		points, err := s.candidates(f)
		if err != nil {
			return err
		}
		log.Printf("Round %d: %d purple/yellow candidates", round+1, len(points))
		rescan := false
		for _, point := range points {
			f, err = s.frame()
			if err != nil {
				return err
			}
			current, err := s.candidates(f)
			if err != nil {
				return err
			}
			present := false
			for _, p := range current {
				if p.Grade == point.Grade && abs(p.X-point.X) < 35 && abs(p.Y-point.Y) < 25 {
					present = true
				}
			}
			if !present {
				log.Print("Truck list moved; rescanning current screen without tapping stale positions")
				rescan = true
				break
			}
			if err = s.Phone.Tap(point.Hit); err != nil {
				return err
			}
			if err = s.Sleep(time.Duration(s.Config.Settle * float64(time.Second))); err != nil {
				return err
			}
			start := time.Now()
			f, err = s.frame()
			if err != nil {
				return err
			}
			if s.require(f, "detail_marker", s.Config.DetailROI) != nil {
				// A selected truck toggles its card closed when tapped again.
				// One bounded re-open is safe only while that same truck is
				// still detected in the list (never tap the Plunder area).
				current, e := s.candidates(f)
				if e != nil {
					return e
				}
				present = false
				for _, p := range current {
					if p.Grade == point.Grade && abs(p.X-point.X) < 35 && abs(p.Y-point.Y) < 25 {
						present = true
					}
				}
				if !present {
					return fmt.Errorf("truck disappeared while opening detail")
				}
				if err = s.Phone.Tap(point.Hit); err != nil {
					return err
				}
				if err = s.Sleep(time.Duration(s.Config.Settle * float64(time.Second))); err != nil {
					return err
				}
				f, err = s.frame()
				if err != nil {
					return err
				}
				if s.require(f, "detail_marker", s.Config.DetailROI) != nil {
					if err = s.require(f, "list_marker", s.Config.ListROI); err != nil {
						return err
					}
					if _, err = s.evidence("unopenable-truck", f); err != nil {
						return err
					}
					log.Printf("WARN: %s truck detail did not open after bounded retry; not a match, checking remaining trucks", point.Grade)
					continue
				}
			}
			o, err := s.inspect(f)
			if err != nil {
				return err
			}
			log.Printf("%s: %d fragment icons, power %d (zero=not needed), inspection %s", point.Grade, o.Fragments, o.Power, time.Since(start).Round(time.Millisecond))
			done, err := s.handle(o)
			if err != nil {
				return err
			}
			if done {
				return nil
			}
			if s.ListChanged {
				break
			}
		}
		if rescan {
			driftRetries++
			if driftRetries >= 5 {
				return fmt.Errorf("truck list keeps changing; stop other phone controls before retrying")
			}
			round--
			continue
		}
		driftRetries = 0
		if s.ListChanged {
			s.ListChanged = false
			round--
			continue
		}
		if maxRefreshes < 0 || round < maxRefreshes {
			f, err = s.frame()
			if err != nil {
				return err
			}
			if err = s.refresh(f); err != nil {
				return err
			}
		}
	}
	log.Print("Refresh limit reached without a match")
	return nil
}
func saveJSON(path string, value any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".state-*.tmp")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(data); err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		return err
	}
	return os.Rename(name, path)
}
func identity(f *Frame, roi Rect) (string, error) {
	mask, err := identityPixels(f, roi)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(mask)
	return hex.EncodeToString(sum[:]), nil
}

func identityPixels(f *Frame, roi Rect) ([]byte, error) {
	part, err := f.crop(roi)
	if err != nil {
		return nil, err
	}
	// Threshold the stable owner/power header, not moving map coordinates.
	mask := make([]byte, len(part.Gray))
	for i, value := range part.Gray {
		if value < 80 {
			mask[i] = 1
		}
	}
	return mask, nil
}

func identityMask(f *Frame, roi Rect) ([]byte, error) {
	pixels, err := identityPixels(f, roi)
	if err != nil {
		return nil, err
	}
	packed := make([]byte, (len(pixels)+7)/8)
	for i, value := range pixels {
		if value != 0 {
			packed[i/8] |= 1 << uint(i%8)
		}
	}
	return packed, nil
}

func sameIdentity(a, b []byte) bool {
	if len(a) == 0 || len(a) != len(b) {
		return false
	}
	changed := 0
	for i := range a {
		changed += bits.OnesCount8(a[i] ^ b[i])
	}
	return float64(changed)/float64(len(a)*8) <= .005
}
