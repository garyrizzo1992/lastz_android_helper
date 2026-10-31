package main

import (
	"bytes"
	"context"
	"fmt"
	"image/png"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

type Phone struct {
	ADB, Serial string
	Context     context.Context
}

func command(ctx context.Context, exe string, args []string, input []byte) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, exe, args...)
	cmd.Stdin = bytes.NewReader(input)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("%s failed: %w: %s", exe, err, strings.TrimSpace(stderr.String()))
	}
	return out, nil
}
func connect(ctx context.Context, adb, serial string) (*Phone, error) {
	out, err := command(ctx, adb, []string{"devices", "-l"}, nil)
	if err != nil {
		return nil, err
	}
	devices := map[string]bool{}
	for _, line := range strings.Split(string(out), "\n") {
		fields := strings.Fields(line)
		if len(fields) > 1 && fields[1] == "device" && strings.Contains(line, "usb:") {
			devices[fields[0]] = true
		}
	}
	if len(devices) == 0 {
		outUSB, e := command(ctx, adb, []string{"-d", "get-serialno"}, nil)
		if e == nil {
			id := strings.TrimSpace(string(outUSB))
			for _, line := range strings.Split(string(out), "\n") {
				fields := strings.Fields(line)
				if len(fields) > 1 && fields[0] == id && fields[1] == "device" {
					devices[id] = true
				}
			}
		}
	}
	if serial != "" {
		for id := range devices {
			if id != serial {
				delete(devices, id)
			}
		}
	}
	if len(devices) != 1 {
		return nil, fmt.Errorf("need one authorized local USB phone; adb devices reports:\n%s", out)
	}
	for id := range devices {
		return &Phone{adb, id, ctx}, nil
	}
	panic("unreachable")
}
func (p *Phone) run(args ...string) ([]byte, error) {
	return command(p.Context, p.ADB, append([]string{"-s", p.Serial}, args...), nil)
}
func (p *Phone) Screenshot() (*Frame, error) {
	out, err := p.run("exec-out", "screencap", "-p")
	if err != nil {
		return nil, err
	}
	img, err := png.Decode(bytes.NewReader(out))
	if err != nil {
		return nil, err
	}
	return newFrame(img), nil
}
func (p *Phone) Tap(h Hit) error {
	_, err := p.run("shell", "input", "tap", strconv.Itoa(h.X), strconv.Itoa(h.Y))
	return err
}
func (p *Phone) Swipe(r Rect) error {
	_, err := p.run("shell", "input", "swipe", strconv.Itoa(r[0]), strconv.Itoa(r[1]), strconv.Itoa(r[2]), strconv.Itoa(r[3]), "500")
	return err
}
func wait(ctx context.Context, d time.Duration) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-time.After(d):
		return nil
	}
}
