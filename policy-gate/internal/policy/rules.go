package policy

import (
	"regexp"
	"strings"
)

type Decision string

const (
	Allow           Decision = "ALLOW"
	Deny            Decision = "DENY"
	RequireApproval Decision = "REQUIRE_APPROVAL"
)

type Match struct {
	Decision Decision
	RuleID   string
	Reason   string
	Category string
}

var riskyTools = map[string]struct{}{
	"exec":         {},
	"bash":         {},
	"shell":        {},
	"write_file":   {},
	"edit_file":    {},
	"send_email":   {},
	"http_request": {},
	"browser":      {},
}

var denyPatterns = []struct {
	re       *regexp.Regexp
	ruleID   string
	category string
	reason   string
}{
	{regexp.MustCompile(`(?i)(ignore (all )?previous instructions|you are now|debug mode|system prompt)`), "R-INJ-01", "prompt_injection", "Prompt injection pattern in content"},
	{regexp.MustCompile(`(?i)(output your (complete )?system prompt|hidden flags?|gateway token)`), "R-INJ-02", "prompt_injection", "System prompt extraction attempt"},
	{regexp.MustCompile(`(?i)(hardcode the real token|real token value)`), "R-INJ-03", "prompt_injection", "Credential extraction via code reframe"},
	{regexp.MustCompile(`(?i)(\.\./|\.\.\\|/etc/passwd|/etc/shadow)`), "R-SBX-01", "sandbox_escape", "Path traversal or sensitive path access"},
	{regexp.MustCompile(`(?i)(printenv|^\s*env\s*$|^\s*env\b|ANTHROPIC_API_KEY|OPENAI_API_KEY|AWS_SECRET)`), "R-CRED-01", "credential_theft", "Environment or secret exfiltration command"},
	{regexp.MustCompile(`(?i)(cat\s+/etc/|read_file:/etc/|~/.openclaw/)`), "R-CRED-02", "credential_theft", "Sensitive config or credential path access"},
	{regexp.MustCompile(`(?i)(SOUL\.md|IDENTITY\.md|USER\.md)`), "R-PERS-01", "persistence", "Agent identity file modification"},
	{regexp.MustCompile(`(?i)(base64\s+-d|decode\()`), "R-EVA-01", "evasion", "Encoded command execution"},
	{regexp.MustCompile(`(?i)(169\.254\.169\.254|metadata\.google|tools\.elevated)`), "R-CFG-01", "config_exploit", "Cloud metadata or elevated tool access"},
}

func profileName(raw string) string {
	if strings.EqualFold(raw, "hardened") {
		return "hardened"
	}
	return "default"
}

func matchContent(content string) *Match {
	trimmed := strings.TrimSpace(content)
	if trimmed == "" {
		return nil
	}
	for _, pattern := range denyPatterns {
		if pattern.re.MatchString(trimmed) {
			return &Match{
				Decision: Deny,
				RuleID:   pattern.ruleID,
				Reason:   pattern.reason,
				Category: pattern.category,
			}
		}
	}
	return nil
}

func matchToolArgs(tool string, args map[string]string) *Match {
	tool = strings.ToLower(strings.TrimSpace(tool))
	blob := strings.ToLower(strings.Join([]string{
		args["command"],
		args["path"],
		args["file"],
		args["url"],
		args["body"],
	}, " "))

	for _, pattern := range denyPatterns {
		if pattern.re.MatchString(blob) {
			return &Match{
				Decision: Deny,
				RuleID:   pattern.ruleID,
				Reason:   pattern.reason,
				Category: pattern.category,
			}
		}
	}

	if profileDenyTool(tool, blob) {
		return &Match{
			Decision: Deny,
			RuleID:   "R-HARD-01",
			Reason:   "Tool blocked by hardened profile",
			Category: "policy",
		}
	}
	return nil
}

func profileDenyTool(tool, blob string) bool {
	switch tool {
	case "exec", "bash", "shell":
		if strings.Contains(blob, "printenv") || strings.Contains(blob, "env") && strings.Contains(blob, "key") {
			return true
		}
	}
	return false
}

func requiresApproval(tool string, profile string) bool {
	if profile == "hardened" {
		if _, ok := riskyTools[strings.ToLower(tool)]; ok {
			return true
		}
	}
	_, risky := riskyTools[strings.ToLower(tool)]
	return risky
}
