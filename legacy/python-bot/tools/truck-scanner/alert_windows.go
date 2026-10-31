//go:build windows

package main

import (
	"fmt"
	"syscall"
	"time"
)

func alertSound() error {
	beep := syscall.NewLazyDLL("user32.dll").NewProc("MessageBeep")
	for i := 0; i < 3; i++ {
		ok, _, err := beep.Call(0x30)
		if ok == 0 {
			return fmt.Errorf("Windows sound failed: %v", err)
		}
		time.Sleep(400 * time.Millisecond)
	}
	return nil
}
