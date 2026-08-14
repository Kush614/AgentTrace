package policy

import (
	"strings"
	"time"

	"github.com/Kush614/AgentTrace/policy-gate/internal/api"
	"github.com/Kush614/AgentTrace/policy-gate/internal/metrics"
)

func Evaluate(req api.EvaluateRequest) api.EvaluateResponse {
	start := time.Now()
	profile := profileName(req.PolicyProfile)

	if req.Arguments == nil {
		req.Arguments = map[string]string{}
	}

	var match *Match
	if req.Content != "" {
		match = matchContent(req.Content)
	}
	if match == nil {
		match = matchToolArgs(req.Tool, req.Arguments)
	}

	resp := api.EvaluateResponse{
		Profile: profile,
	}

	if match != nil {
		resp.Decision = string(match.Decision)
		resp.RuleID = match.RuleID
		resp.Reason = match.Reason
		resp.Category = firstNonEmpty(match.Category, req.CategoryHint)
	} else if requiresApproval(req.Tool, profile) {
		resp.Decision = string(RequireApproval)
		resp.RuleID = "R-APP-01"
		resp.Reason = "Risky tool requires human approval"
		resp.Category = firstNonEmpty(req.CategoryHint, "approval_rail")
	} else {
		resp.Decision = string(Allow)
		resp.RuleID = "R-ALLOW-00"
		resp.Reason = "No policy violation detected"
		resp.Category = req.CategoryHint
	}

	resp.LatencyMS = float64(time.Since(start).Microseconds()) / 1000.0
	metrics.Record(resp.Decision, resp.LatencyMS)
	return resp
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if strings.TrimSpace(v) != "" {
			return v
		}
	}
	return ""
}
