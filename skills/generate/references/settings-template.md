# Settings Template

## Configuration Scopes & Precedence

| Scope | Location | Who | Shared | Precedence |
|---|---|---|---|---|
| Managed | Server-managed, MDM/OS, or system `managed-settings.json` | All users | Yes (IT) | Highest |
| User | `~/.claude/settings.json` | You, all projects | No | |
| User local | `~/.claude/settings.local.json` | You, all projects | No | |
| Project | `.claude/settings.json` | All collaborators | Yes (git) | |
| Project local | `.claude/settings.local.json` | You, this repo | No (gitignored) | Lowest* |

*Local project > shared project > user settings. Managed always wins. Array settings merge (concatenated, deduplicated).

## Permissions

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test:*)",
      "Bash(git status:*)",
      "Read",
      "mcp__server__tool_name",
      "Skill(deploy)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)"
    ],
    "defaultMode": "normal",
    "disableBypassPermissionsMode": "disable",
    "additionalDirectories": ["/path/to/shared-lib"]
  }
}
```

Evaluation order: deny (first) → ask → allow.

Rule syntax: `Tool` or `Tool(specifier)`.

## Sandbox Settings

```json
{
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": false,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["docker"],
    "filesystem": {
      "allowWrite": ["/tmp"],
      "denyWrite": ["/etc"],
      "denyRead": ["/secrets"],
      "allowRead": ["/shared"]
    },
    "network": {
      "allowedDomains": ["api.example.com"],
      "allowUnixSockets": false,
      "allowLocalBinding": false
    }
  }
}
```

## Plugin Configuration

```json
{
  "enabledPlugins": {
    "plugin-name@marketplace-name": true
  },
  "extraKnownMarketplaces": {
    "marketplace-name": {
      "source": {
        "source": "github",
        "repo": "owner/repo"
      }
    }
  },
  "strictKnownMarketplaces": {
    "allowed-marketplace": true
  }
}
```

`strictKnownMarketplaces` is managed-only (admin-controlled allowlist).

## Subagent Configuration

| Location | Scope |
|---|---|
| `~/.claude/agents/` | Personal subagents (all projects) |
| `.claude/agents/` | Project subagents (committed) |

## Key Settings Reference

| Setting | Description |
|---|---|
| `model` | Default model override |
| `availableModels` | Restrict available models |
| `effortLevel` | Default effort level |
| `defaultShell` | Shell for Bash tool |
| `env` | Environment variables |
| `hooks` | Hook configuration |
| `autoMemoryEnabled` / `autoMemoryDirectory` | Auto memory control |
| `claudeMdExcludes` | Skip specific CLAUDE.md files |
| `enableAllProjectMcpServers` | Auto-enable project MCP servers |
| `allowedMcpServers` / `deniedMcpServers` | MCP policy control |
| `allowManagedHooksOnly` | Managed-only: restrict hooks to managed/force-enabled plugin hooks |
| `language` | UI language |
| `statusLine` | Custom status line command |
| `refreshInterval` | Re-run status line command every N seconds |
| `respectGitignore` | Honor .gitignore in file operations |
| `plansDirectory` | Custom plans storage location |

## Best Practices

- Scope permissions narrowly: `Bash(npm test:*)` not `Bash(*)`
- Put machine-specific paths in `.local.json` (gitignored)
- Never store secrets in settings files
- Keep project settings minimal — only project-specific overrides
- User-level settings for personal preferences and global plugins
- Use sandbox for additional security on sensitive projects
- Use `deny` rules for dangerous operations before `allow` rules
- `additionalDirectories` for monorepo or shared library access
