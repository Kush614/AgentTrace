package metrics

import (
	"math"
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

const sampleCap = 4096

var (
	startedAt      = time.Now()
	requestsTotal  atomic.Int64
	decisionCounts sync.Map
	latencyMu      sync.Mutex
	latencySamples []float64
)

func Record(decision string, latencyMS float64) {
	requestsTotal.Add(1)
	if v, ok := decisionCounts.Load(decision); ok {
		decisionCounts.Store(decision, v.(int64)+1)
	} else {
		decisionCounts.Store(decision, int64(1))
	}

	latencyMu.Lock()
	defer latencyMu.Unlock()
	if len(latencySamples) >= sampleCap {
		latencySamples = latencySamples[1:]
	}
	latencySamples = append(latencySamples, latencyMS)
}

func Snapshot() (total int64, decisions map[string]int64, latency map[string]float64, uptime float64) {
	total = requestsTotal.Load()
	decisions = map[string]int64{}
	decisionCounts.Range(func(key, value any) bool {
		decisions[key.(string)] = value.(int64)
		return true
	})

	latencyMu.Lock()
	samples := append([]float64(nil), latencySamples...)
	latencyMu.Unlock()

	latency = map[string]float64{
		"p50": percentile(samples, 0.50),
		"p95": percentile(samples, 0.95),
		"p99": percentile(samples, 0.99),
		"max": maxSample(samples),
	}
	uptime = time.Since(startedAt).Seconds()
	return total, decisions, latency, uptime
}

func percentile(samples []float64, p float64) float64 {
	if len(samples) == 0 {
		return 0
	}
	sorted := append([]float64(nil), samples...)
	sort.Float64s(sorted)
	idx := int(math.Ceil(p*float64(len(sorted)))) - 1
	if idx < 0 {
		idx = 0
	}
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}

func maxSample(samples []float64) float64 {
	if len(samples) == 0 {
		return 0
	}
	max := samples[0]
	for _, v := range samples[1:] {
		if v > max {
			max = v
		}
	}
	return max
}
