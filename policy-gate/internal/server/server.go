package server

import (
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/Kush614/AgentTrace/policy-gate/internal/api"
	"github.com/Kush614/AgentTrace/policy-gate/internal/metrics"
	"github.com/Kush614/AgentTrace/policy-gate/internal/policy"
)

type Server struct {
	mux       sync.Mutex
	approvals map[string]bool
}

func New() *Server {
	return &Server{approvals: map[string]bool{}}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.handleHealth)
	mux.HandleFunc("GET /metrics", s.handleMetrics)
	mux.HandleFunc("GET /v1/metrics", s.handleMetrics)
	mux.HandleFunc("POST /v1/evaluate", s.handleEvaluate)
	mux.HandleFunc("POST /v1/approval", s.handleApproval)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"service": "policy-gate",
	})
}

func (s *Server) handleMetrics(w http.ResponseWriter, _ *http.Request) {
	total, decisions, latency, uptime := metrics.Snapshot()
	writeJSON(w, http.StatusOK, api.MetricsResponse{
		RequestsTotal: total,
		Decisions:     decisions,
		LatencyMS:     latency,
		UptimeSeconds: uptime,
	})
}

func (s *Server) handleEvaluate(w http.ResponseWriter, r *http.Request) {
	var req api.EvaluateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body"})
		return
	}
	if req.Tool == "" && req.Content == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "tool or content is required"})
		return
	}
	writeJSON(w, http.StatusOK, policy.Evaluate(req))
}

func (s *Server) handleApproval(w http.ResponseWriter, r *http.Request) {
	var req api.ApprovalRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body"})
		return
	}
	if req.ApprovalID == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "approval_id is required"})
		return
	}

	s.mux.Lock()
	s.approvals[req.ApprovalID] = req.Approved
	s.mux.Unlock()

	status := "denied"
	if req.Approved {
		status = "approved"
	}
	metrics.Record("APPROVAL_"+status, 0)

	writeJSON(w, http.StatusOK, api.ApprovalResponse{
		ApprovalID: req.ApprovalID,
		Status:     status,
		ExpiresAt:  time.Now().Add(5 * time.Minute).UTC().Format(time.RFC3339),
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}
