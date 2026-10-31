package main

import (
	"bytes"
	"context"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"math"
	"regexp"
	"strconv"
	"strings"
)

var powerPattern = regexp.MustCompile(`^(\d+(?:\.\d+)?)([KMB])$`)
var rawPowerPattern = regexp.MustCompile(`^(?:\d{7,10}|\d{1,3}(?:,\d{3}){2,3})$`)

func parsePower(text string) (int64, bool) {
	text = strings.ToUpper(strings.ReplaceAll(strings.TrimSpace(text), " ", ""))
	var n int64
	if m := powerPattern.FindStringSubmatch(text); m != nil {
		v, e := strconv.ParseFloat(m[1], 64)
		if e != nil {
			return 0, false
		}
		n = int64(math.Round(v * map[string]float64{"K": 1e3, "M": 1e6, "B": 1e9}[m[2]]))
	} else if rawPowerPattern.MatchString(text) {
		v, e := strconv.ParseInt(strings.ReplaceAll(text, ",", ""), 10, 64)
		if e != nil {
			return 0, false
		}
		n = v
	} else {
		return 0, false
	}
	return n, n > 0 && n <= 9_999_999_999
}
func ocr(ctx context.Context, exe string, f *Frame, psm string, whiteScale int, whitelist string) (string, error) {
	var img image.Image = f.Img
	if whiteScale > 0 {
		// Fit the text tightly so word-mode OCR retains its K/M/B suffix.
		bounds := image.Rectangle{Min: image.Pt(f.W, f.H), Max: image.Point{}}
		for y := 0; y < f.H; y++ {
			for x := 0; x < f.W; x++ {
				_, s, v := hsv(f.Img.NRGBAAt(x, y))
				if s <= 90 && v >= 170 {
					if x < bounds.Min.X {
						bounds.Min.X = x
					}
					if y < bounds.Min.Y {
						bounds.Min.Y = y
					}
					if x+1 > bounds.Max.X {
						bounds.Max.X = x + 1
					}
					if y+1 > bounds.Max.Y {
						bounds.Max.Y = y + 1
					}
				}
			}
		}
		if bounds.Empty() {
			return "", fmt.Errorf("no white power text found")
		}
		out := image.NewGray(image.Rect(0, 0, (bounds.Dx()+20)*whiteScale, (bounds.Dy()+20)*whiteScale))
		for i := range out.Pix {
			out.Pix[i] = 255
		}
		for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
			for x := bounds.Min.X; x < bounds.Max.X; x++ {
				_, s, v := hsv(f.Img.NRGBAAt(x, y))
				if s <= 90 && v >= 170 {
					for dy := 0; dy < whiteScale; dy++ {
						for dx := 0; dx < whiteScale; dx++ {
							out.SetGray((x-bounds.Min.X+10)*whiteScale+dx, (y-bounds.Min.Y+10)*whiteScale+dy, color.Gray{0})
						}
					}
				}
			}
		}
		img = out
	}
	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		return "", err
	}
	args := []string{"stdin", "stdout", "--psm", psm}
	if whitelist != "" {
		args = append(args, "-c", "tessedit_char_whitelist="+whitelist)
	}
	out, err := command(ctx, exe, args, buf.Bytes())
	return strings.TrimSpace(string(out)), err
}
func powerOCR(ctx context.Context, exe string, f *Frame, powerLimit int64) (int64, error) {
	counts := map[int64]int{}
	var readings []int64
	// Different segmentation modes, not repeated scales of the same model:
	// line-mode at 3x/4x consistently misread a real leading 5 as 9.
	for _, strategy := range []struct {
		PSM   string
		Scale int
	}{{"8", 2}, {"7", 2}, {"13", 3}} {
		text, err := ocr(ctx, exe, f, strategy.PSM, strategy.Scale, "0123456789.,KMB")
		if err != nil {
			return 0, err
		}
		if value, ok := parsePower(text); ok {
			counts[value]++
			readings = append(readings, value)
			if counts[value] >= 2 {
				if powerLimit > 0 {
					for _, other := range readings {
						if (other < powerLimit) != (value < powerLimit) {
							return 0, fmt.Errorf("power OCR readings straddle alert limit: %v", readings)
						}
					}
				}
				return value, nil
			}
		}
	}
	return 0, fmt.Errorf("power OCR did not produce two agreeing values")
}
