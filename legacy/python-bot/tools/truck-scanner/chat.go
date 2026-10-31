package main

import (
	"fmt"
	"log"
	"regexp"
	"strings"
	"time"
)

func (s *Scanner) tapTemplate(f *Frame, name string, roi Rect) error {
	h, err := unique(s.hits(f, name, roi), name)
	if err != nil {
		return err
	}
	return s.Phone.Tap(h)
}
func (s *Scanner) verifyWorldPost(power int64, state string, fragments int) (string, error) {
	f, err := s.frame()
	if err != nil {
		return "", err
	}
	if err = s.require(f, "list_marker", s.Config.ListROI); err != nil {
		return "", err
	}
	if err = s.tapTemplate(f, "truck_back", Rect{0, 1400, 120, f.H}); err != nil {
		return "", err
	}
	if err = s.Sleep(800 * time.Millisecond); err != nil {
		return "", err
	}
	f, err = s.frame()
	if err != nil {
		return "", err
	}
	if err = s.require(f, "truck_entry", Rect{0, 900, 110, 1220}); err != nil {
		return "", err
	}
	if err = s.Phone.Tap(Hit{X: s.Config.ChatOpenPoint[0], Y: s.Config.ChatOpenPoint[1]}); err != nil {
		return "", err
	}
	if err = s.Sleep(time.Second); err != nil {
		return "", err
	}
	f, err = s.frame()
	if err != nil {
		return "", err
	}
	worldTab := Rect{0, 140, f.W, 225}
	if len(s.hits(f, "chat_world_selected", worldTab)) != 1 {
		if err = s.tapTemplate(f, "chat_world_tab", worldTab); err != nil {
			return "", err
		}
		if err = s.Sleep(500 * time.Millisecond); err != nil {
			return "", err
		}
		f, err = s.frame()
		if err != nil {
			return "", err
		}
	}
	if err = s.require(f, "chat_world_selected", worldTab); err != nil {
		return "", err
	}
	path, err := s.evidence("world-chat-receipt", f)
	if err != nil {
		return "", err
	}
	if err = s.findWorldCard(f, power, state, fragments); err != nil {
		return path, err
	}
	log.Printf("Matching World chat card verified for state %s, power %d, %d fragment icons", state, power, fragments)
	s.ReceiptVerified = true
	// Restore the list before the scanner resumes selecting trucks.
	if err = s.tapTemplate(f, "chat_back", Rect{0, 1400, 120, f.H}); err != nil {
		return path, err
	}
	if err = s.Sleep(800 * time.Millisecond); err != nil {
		return path, err
	}
	f, err = s.frame()
	if err != nil {
		return path, err
	}
	if err = s.tapTemplate(f, "truck_entry", Rect{0, 900, 110, 1220}); err != nil {
		return path, err
	}
	if err = s.Sleep(time.Second); err != nil {
		return path, err
	}
	f, err = s.frame()
	if err != nil {
		return path, err
	}
	err = s.require(f, "list_marker", s.Config.ListROI)
	if err == nil {
		s.ListChanged = true
	}
	return path, err
}
func (s *Scanner) findWorldCard(f *Frame, power int64, state string, fragments int) error {
	if err := s.require(f, "chat_world_selected", Rect{0, 140, f.W, 225}); err != nil {
		return err
	}
	for _, header := range s.hits(f, "chat_truck_header", Rect{100, 320, f.W - 80, 1400}) {
		powerROI := Rect{header.X + 83, header.Y - 18, min(f.W, header.X+225), header.Y + 20}
		part, err := f.crop(powerROI)
		if err != nil {
			continue
		}
		actual, e := s.ReadPower(part)
		if e != nil || actual != power {
			continue
		}
		textROI := Rect{max(0, header.X-40), header.Y + 18, min(f.W, header.X+350), min(f.H, header.Y+80)}
		part, err = f.crop(textROI)
		if err != nil {
			continue
		}
		text, e := s.ReadText(part, "6", 0, "")
		if e != nil {
			return e
		}
		normalized := strings.ToLower(strings.Join(strings.Fields(text), ""))
		if !regexp.MustCompile(`state` + regexp.QuoteMeta(state) + `(?:\D|$)`).MatchString(normalized) {
			continue
		}
		cargo := Rect{max(0, header.X-45), header.Y + 80, min(f.W, header.X+300), min(f.H, header.Y+175)}
		if len(s.hits(f, "chat_fragment", cargo)) == fragments {
			return nil
		}
	}
	return fmt.Errorf("matching %d-fragment World chat card not found; do not repost blindly", fragments)
}
