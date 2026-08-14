package api

type EvaluateRequest struct {
	AgentID       string            `json:"agent_id"`
	SessionID     string            `json:"session_id"`
	Tool          string            `json:"tool"`
	Arguments     map[string]string `json:"arguments"`
	Content       string            `json:"content,omitempty"`
	PolicyProfile string            `json:"policy_profile,omitempty"`
	CategoryHint  string            `json:"category_hint,omitempty"`
}

type EvaluateResponse struct {
	Decision   string `json:"decision"`
	RuleID     string `json:"rule_id"`
	Reason     string `json:"reason"`
	Category   string `json:"category,omitempty"`
	LatencyMS  float64 `json:"latency_ms"`
	Profile    string `json:"profile"`
}

type ApprovalRequest struct {
	ApprovalID string `json:"approval_id"`
	AgentID    string `json:"agent_id"`
	Tool       string `json:"tool"`
	Approved   bool   `json:"approved"`
	Reviewer   string `json:"reviewer,omitempty"`
}

type ApprovalResponse struct {
	ApprovalID string `json:"approval_id"`
	Status     string `json:"status"`
	ExpiresAt  string `json:"expires_at,omitempty"`
}

type MetricsResponse struct {
	RequestsTotal int64              `json:"requests_total"`
	Decisions     map[string]int64   `json:"decisions"`
	LatencyMS     map[string]float64 `json:"latency_ms"`
	UptimeSeconds float64            `json:"uptime_seconds"`
}
