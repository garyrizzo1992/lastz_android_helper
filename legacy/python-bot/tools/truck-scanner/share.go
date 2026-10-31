package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"regexp"
	"strings"
	"time"
)

type ShareRecord struct {
	State       string    `json:"state"`
	AttemptedAt time.Time `json:"attempted_at"`
	Evidence    string    `json:"evidence"`
	Power       int64     `json:"power"`
	Fragments   int       `json:"fragments"`
	Coordinates string    `json:"coordinates"`
	OwnerMask   []byte    `json:"owner_mask,omitempty"`
}
type ShareState struct {
	Targets  map[string]ShareRecord `json:"targets"`
	LastSent time.Time              `json:"last_sent"`
}

var coordinatesPattern = regexp.MustCompile(`#?(\d+)X:?(\d+)Y:?(\d+)`)

func parseShareCoordinates(text string) (string, error) {
	text = strings.ToUpper(strings.Join(strings.Fields(text), ""))
	m := coordinatesPattern.FindStringSubmatch(text)
	if m == nil {
		return "", fmt.Errorf("share coordinates unreadable: %q", text)
	}
	return "state-" + m[1] + "-x-" + m[2] + "-y-" + m[3], nil
}
func (s *Scanner) shareIdentity(f *Frame) (string, error) {
	part, err := f.crop(s.Config.ShareIdentityROI)
	if err != nil {
		return "", err
	}
	text, err := s.ReadText(part, "7", 0, "0123456789XY#:")
	if err != nil {
		return "", err
	}
	return parseShareCoordinates(text)
}

// The globe is the anchor. Button row numbers and absolute coordinates are
// deliberately not used: only a unique share control aligned with that globe.
func worldButton(world []Hit, buttons []Hit) (Hit, error) {
	anchor, err := unique(world, "World globe icon")
	if err != nil {
		return Hit{}, err
	}
	var aligned []Hit
	for _, button := range buttons {
		if button.X > anchor.X+80 && abs(button.Y-anchor.Y) <= 25 {
			aligned = append(aligned, button)
		}
	}
	return unique(aligned, "share button aligned with World icon")
}

func (s *Scanner) worldMenuControls(f *Frame) (Hit, Hit, error) {
	if _, err := unique(s.hits(f, "share_close", s.all(f)), "Share menu close control"); err != nil {
		return Hit{}, Hit{}, err
	}
	globe, err := unique(s.hits(f, "world_icon", s.all(f)), "World globe icon")
	if err != nil {
		return Hit{}, Hit{}, err
	}
	button, err := worldButton([]Hit{globe}, s.hits(f, "share_button", s.all(f)))
	return button, globe, err
}

func (s *Scanner) worldLabel(f *Frame, globe Hit) error {
	label, err := f.crop(Rect{globe.X + 50, max(0, globe.Y-35), min(f.W, globe.X+260), min(f.H, globe.Y+35)})
	if err != nil {
		return err
	}
	text, err := s.ReadText(label, "7", 0, "")
	if err != nil {
		return err
	}
	if strings.ToLower(strings.TrimSpace(text)) != "world" {
		return fmt.Errorf("World icon label not confirmed: %q", text)
	}
	return nil
}

func (s *Scanner) waitWorldMenu() (*Frame, Hit, error) {
	var last *Frame
	var lastErr error
	for attempt := 0; attempt < 5; attempt++ {
		f, err := s.frame()
		if err != nil {
			return nil, Hit{}, err
		}
		last = f
		button, globe, err := s.worldMenuControls(f)
		if err == nil {
			err = s.worldLabel(f, globe)
		}
		if err == nil {
			return f, button, nil
		}
		lastErr = err
		if attempt < 4 {
			if err = s.Sleep(200 * time.Millisecond); err != nil {
				return nil, Hit{}, err
			}
		}
	}
	if last != nil {
		if _, err := s.evidence("world-share-menu-unrecognized", last); err != nil {
			return nil, Hit{}, err
		}
	}
	return nil, Hit{}, fmt.Errorf("World share menu did not become ready after five observations: %w", lastErr)
}
func (s *Scanner) shareWorld(o Observation) error {
	if !worldTarget(o, s.Config) {
		return fmt.Errorf("truck does not meet a configured World-sharing rule")
	}
	powerPart, err := o.Frame.crop(s.Config.PowerROI)
	if err != nil {
		return err
	}
	expectedPower := o.Power
	if expectedPower == 0 {
		expectedPower, err = s.ReadPower(powerPart)
		if err != nil {
			return err
		}
	} // identity/receipt only for two-icon shares
	owner, err := identity(o.Frame, s.Config.TruckIdentityROI)
	if err != nil {
		return err
	}
	ownerMask, err := identityMask(o.Frame, s.Config.TruckIdentityROI)
	if err != nil {
		return err
	}
	entry, err := unique(s.hits(o.Frame, "share_entry", s.Config.ShareEntryROI), "truck Share")
	if err != nil {
		return err
	}
	if err = s.Phone.Tap(entry); err != nil {
		return err
	}
	if err = s.Sleep(500 * time.Millisecond); err != nil {
		return err
	}
	menu, button, err := s.waitWorldMenu()
	if err != nil {
		return err
	}
	coordinates, err := s.shareIdentity(menu)
	if err != nil {
		return err
	}
	stateNumber := strings.Split(coordinates, "-")[1]
	menuOwner, err := identityMask(menu, s.Config.ShareIdentityROI)
	if err != nil {
		return err
	}
	id := "state-" + stateNumber + "-owner-" + owner
	state := ShareState{Targets: map[string]ShareRecord{}}
	data, readErr := os.ReadFile(s.StatePath)
	if readErr == nil {
		if err = json.Unmarshal(data, &state); err != nil {
			return fmt.Errorf("share ledger unreadable: %w", err)
		}
	} else if !os.IsNotExist(readErr) {
		return readErr
	}
	if state.Targets == nil {
		state.Targets = map[string]ShareRecord{}
	}
	// Anti-aliasing can vary a few pixels between screenshots. Reuse an
	// existing same-state/same-power owner record when its mask is equivalent.
	if _, exists := state.Targets[id]; !exists {
		for key, record := range state.Targets {
			if strings.HasPrefix(key, "state-"+stateNumber+"-owner-") && record.Power == expectedPower && sameIdentity(ownerMask, record.OwnerMask) {
				id = key
				break
			}
		}
	}
	if previous, exists := state.Targets[id]; exists && previous.State != "cancelled_before_send" && time.Since(previous.AttemptedAt) < 24*time.Hour {
		log.Printf("World share skipped: this truck already has a %s record", previous.State)
		close, err := unique(s.hits(menu, "share_close", s.all(menu)), "Share close")
		if err != nil {
			return err
		}
		return s.Phone.Tap(close)
	}
	if delay := time.Duration(s.Config.ShareInterval*float64(time.Second)) - time.Since(state.LastSent); delay > 0 {
		if err = s.Sleep(delay); err != nil {
			return err
		}
	}
	// Save BEFORE the external write. Unknown outcomes are never blindly sent
	// again, including after restart; screenshots and ledger allow manual review.
	path, err := s.evidence("world-share-before", menu)
	if err != nil {
		return err
	}
	record := ShareRecord{State: "pending", AttemptedAt: time.Now(), Evidence: path, Power: expectedPower, Fragments: o.Fragments, Coordinates: coordinates, OwnerMask: ownerMask}
	state.Targets[id] = record
	if err = saveJSON(s.StatePath, state); err != nil {
		return err
	}
	// Re-read the globe and button after any rate-limit wait, not a stale tap.
	menu, button, err = s.waitWorldMenu()
	if err != nil {
		return err
	}
	freshID, err := identityMask(menu, s.Config.ShareIdentityROI)
	if err != nil {
		return err
	}
	if !sameIdentity(freshID, menuOwner) {
		return fmt.Errorf("truck identity changed before World share")
	}
	if err = s.Phone.Tap(button); err != nil {
		return err
	}
	if err = s.Sleep(400 * time.Millisecond); err != nil {
		return err
	}
	confirmation, err := s.frame()
	if err != nil {
		return err
	}
	if len(s.hits(confirmation, "world_confirm_icon", s.all(confirmation))) > 0 {
		confirm, err := s.worldConfirmation(confirmation)
		if err != nil {
			return err
		}
		if _, err = s.evidence("world-share-confirmation", confirmation); err != nil {
			return err
		}
		record.State = "send_attempted"
		state.Targets[id] = record
		if err = saveJSON(s.StatePath, state); err != nil {
			return err
		}
		if err = s.Phone.Tap(confirm); err != nil {
			return err
		}
	}
	confirmed := false
	for attempt := 0; attempt < 4; attempt++ {
		if err = s.Sleep(150 * time.Millisecond); err != nil {
			return err
		}
		after, e := s.frame()
		if e != nil {
			return e
		}
		path, err = s.evidence(fmt.Sprintf("world-share-after-%d", attempt), after)
		if err != nil {
			return err
		}
		// Success toast is required, not just disappearance of the menu.
		text, e := s.ReadText(after, "11", 0, "")
		if e != nil {
			return e
		}
		lower := strings.ToLower(text)
		if strings.Contains(lower, "shared successfully") || strings.Contains(lower, "share successfully") || strings.Contains(lower, "successfully shared") {
			confirmed = true
			break
		}
	}
	if !confirmed {
		s.ReceiptVerified = false
		path, err = s.verifyWorldPost(expectedPower, stateNumber, o.Fragments)
		confirmed = s.ReceiptVerified
		if err != nil {
			log.Printf("World chat receipt not verified: %v", err)
		}
	}
	restoreErr := err
	record.Evidence = path
	record.State = "uncertain"
	if confirmed {
		record.State = "verified"
		state.LastSent = time.Now()
	}
	state.Targets[id] = record
	if err = saveJSON(s.StatePath, state); err != nil {
		return err
	}
	if !confirmed {
		return fmt.Errorf("World share attempted but confirmation was not verified; not sending twice; inspect %s", path)
	}
	log.Printf("WORLD SHARE VERIFIED: %d Universal Orange Hero Fragment icons; power %d; evidence %s", o.Fragments, expectedPower, path)
	return restoreErr
}

func (s *Scanner) worldConfirmation(f *Frame) (Hit, error) {
	globe, err := unique(s.hits(f, "world_confirm_icon", s.all(f)), "confirmation World globe")
	if err != nil {
		return Hit{}, err
	}
	label, err := unique(s.hits(f, "world_confirm_label", s.all(f)), "confirmation World label")
	if err != nil {
		return Hit{}, err
	}
	if abs(label.X-globe.X) > 40 || label.Y <= globe.Y || label.Y-globe.Y > 120 {
		return Hit{}, fmt.Errorf("World label not associated with confirmation globe")
	}
	button, err := unique(s.hits(f, "world_confirm_share", s.all(f)), "gold Share confirmation")
	if err != nil {
		return Hit{}, err
	}
	cancel, err := unique(s.hits(f, "world_confirm_cancel", s.all(f)), "Cancel control")
	if err != nil {
		return Hit{}, err
	}
	if button.X >= globe.X || cancel.X <= globe.X || abs(cancel.Y-button.Y) > 15 || button.Y <= label.Y {
		return Hit{}, fmt.Errorf("unexpected World confirmation layout")
	}
	return button, nil
}
