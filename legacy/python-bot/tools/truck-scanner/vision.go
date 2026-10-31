package main

import (
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"math"
	"sort"
)

type Rect [4]int

func (r Rect) Bounds() image.Rectangle { return image.Rect(r[0], r[1], r[2], r[3]) }

type Frame struct {
	Img  *image.NRGBA
	Gray []float64
	W, H int
}
type Hit struct {
	X, Y  int
	Score float64
}

func newFrame(img image.Image) *Frame {
	b := img.Bounds()
	out := image.NewNRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	draw.Draw(out, out.Bounds(), img, b.Min, draw.Src)
	f := &Frame{Img: out, W: b.Dx(), H: b.Dy(), Gray: make([]float64, b.Dx()*b.Dy())}
	for y := 0; y < f.H; y++ {
		for x := 0; x < f.W; x++ {
			p := out.NRGBAAt(x, y)
			f.Gray[y*f.W+x] = .299*float64(p.R) + .587*float64(p.G) + .114*float64(p.B)
		}
	}
	return f
}
func (f *Frame) valid(r Rect) bool {
	return r[0] >= 0 && r[1] >= 0 && r[2] > r[0] && r[3] > r[1] && r[2] <= f.W && r[3] <= f.H
}
func (f *Frame) crop(r Rect) (*Frame, error) {
	if !f.valid(r) {
		return nil, fmt.Errorf("ROI outside screenshot: %v", r)
	}
	return newFrame(f.Img.SubImage(r.Bounds())), nil
}

type sample struct {
	X, Y int
	V    float64
}

func templateSamples(t *Frame) ([]sample, float64) {
	step := 3
	if t.W*t.H < 1600 {
		step = 2
	}
	var samples []sample
	sum := 0.
	for y := 0; y < t.H; y += step {
		for x := 0; x < t.W; x += step {
			v := t.Gray[y*t.W+x]
			samples = append(samples, sample{x, y, v})
			sum += v
		}
	}
	mean := sum / float64(len(samples))
	variance := 0.
	for i := range samples {
		samples[i].V -= mean
		variance += samples[i].V * samples[i].V
	}
	return samples, variance
}
func correlation(f *Frame, x, y int, samples []sample, variance float64) float64 {
	sum, squares, dot := 0., 0., 0.
	for _, p := range samples {
		v := f.Gray[(y+p.Y)*f.W+x+p.X]
		sum += v
		squares += v * v
		dot += v * p.V
	}
	v := squares - sum*sum/float64(len(samples))
	if v <= 0 || variance <= 0 {
		return -1
	}
	return dot / math.Sqrt(v*variance)
}
func match(f, t *Frame, roi Rect, threshold float64) []Hit {
	if !f.valid(roi) || t == nil || roi[2]-roi[0] < t.W || roi[3]-roi[1] < t.H {
		return nil
	}
	samples, variance := templateSamples(t)
	if variance < 1 {
		return nil
	}
	var seeds []Hit
	// Sampled NCC, coarse-to-fine. No OpenCV, Python, CGO or fixed truck taps.
	for y := roi[1]; y <= roi[3]-t.H; y += 3 {
		for x := roi[0]; x <= roi[2]-t.W; x += 3 {
			score := correlation(f, x, y, samples, variance)
			if score >= .40 {
				seeds = append(seeds, Hit{x, y, score})
			}
		}
	}
	sort.Slice(seeds, func(i, j int) bool { return seeds[i].Score > seeds[j].Score })
	var hits []Hit
	for _, seed := range seeds {
		if len(hits) >= 40 {
			break
		}
		skip := false
		for _, h := range hits {
			if abs(seed.X+t.W/2-h.X) < max(12, t.W/2) && abs(seed.Y+t.H/2-h.Y) < max(12, t.H/2) {
				skip = true
				break
			}
		}
		if skip {
			continue
		}
		best := Hit{Score: -1}
		for y := max(roi[1], seed.Y-2); y <= min(roi[3]-t.H, seed.Y+2); y++ {
			for x := max(roi[0], seed.X-2); x <= min(roi[2]-t.W, seed.X+2); x++ {
				score := correlation(f, x, y, samples, variance)
				if score > best.Score {
					best = Hit{x + t.W/2, y + t.H/2, score}
				}
			}
		}
		if best.Score >= threshold {
			hits = append(hits, best)
		}
	}
	return hits
}
func abs(v int) int {
	if v < 0 {
		return -v
	}
	return v
}
func difference(a, b *Frame, r Rect) float64 {
	if !a.valid(r) || !b.valid(r) {
		return math.Inf(1)
	}
	sum := 0.
	for y := r[1]; y < r[3]; y++ {
		for x := r[0]; x < r[2]; x++ {
			pa, pb := a.Img.NRGBAAt(x, y), b.Img.NRGBAAt(x, y)
			sum += float64(abs(int(pa.R)-int(pb.R)) + abs(int(pa.G)-int(pb.G)) + abs(int(pa.B)-int(pb.B)))
		}
	}
	return sum / float64((r[2]-r[0])*(r[3]-r[1])*3)
}
func hsv(p color.NRGBA) (float64, float64, float64) {
	r, g, b := float64(p.R)/255, float64(p.G)/255, float64(p.B)/255
	hi, lo := math.Max(r, math.Max(g, b)), math.Min(r, math.Min(g, b))
	delta := hi - lo
	h, s := 0., 0.
	if hi > 0 {
		s = delta / hi
	}
	if delta > 0 {
		switch hi {
		case r:
			h = math.Mod((g-b)/delta, 6)
		case g:
			h = (b-r)/delta + 2
		default:
			h = (r-g)/delta + 4
		}
		h *= 30
		if h < 0 {
			h += 180
		}
	}
	return h, s * 255, hi * 255
}
func gradeRatio(f, t *Frame, h Hit, purple bool) float64 {
	good, total := 0, 0
	for y := h.Y - t.H/2; y < h.Y+(t.H+1)/2; y++ {
		for x := h.X - t.W/2; x < h.X+(t.W+1)/2; x++ {
			if x < 0 || y < 0 || x >= f.W || y >= f.H {
				continue
			}
			hue, s, v := hsv(f.Img.NRGBAAt(x, y))
			total++
			if purple && hue >= 125 && hue <= 170 && s >= 80 && v >= 90 || !purple && hue >= 12 && hue <= 38 && s >= 100 && v >= 120 {
				good++
			}
		}
	}
	if total == 0 {
		return 0
	}
	return float64(good) / float64(total)
}
