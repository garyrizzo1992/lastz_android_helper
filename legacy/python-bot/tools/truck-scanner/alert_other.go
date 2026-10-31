//go:build !windows

package main

import "fmt"

func alertSound() error { fmt.Print("\a\a\a"); return nil }
