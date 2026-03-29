# CLAUDE.md Review Checklist

## File Discovery
- [ ] Project root `CLAUDE.md` exists (at `./CLAUDE.md` or `./.claude/CLAUDE.md`)
- [ ] Module-level `CLAUDE.md` files exist where appropriate (large subdirectories with distinct conventions)
- [ ] `.claude/rules/` directory used for path-specific rules (if applicable)

## Structure
- [ ] Has clear sections (overview, conventions, commands, patterns, constraints)
- [ ] Uses markdown headers and bullets for scanability
- [ ] Not a wall of text — structured with lists and short paragraphs

## Content Quality
- [ ] Uses imperative tone ("Use X", "Never do Y") — not descriptive ("This project uses X")
- [ ] Instructions are actionable, specific, and verifiable
- [ ] No vague guidance ("be careful", "use best practices")
- [ ] No stale or contradictory instructions
- [ ] No information Claude already knows (language basics, common patterns)

## Imports (`@path` syntax)
- [ ] `@path/to/file` references point to existing files
- [ ] Import chains do not exceed 5 hops
- [ ] No circular imports
- [ ] `@AGENTS.md` used if project has an AGENTS.md (compatibility)

## Rules Directory (`.claude/rules/`)
- [ ] Each rule file covers one topic
- [ ] Rules without `paths` frontmatter are loaded at launch (global rules)
- [ ] Path-specific rules use correct YAML frontmatter with valid glob patterns
- [ ] No duplicate or conflicting rules across files

## Context Window Efficiency
- [ ] Target under 200 lines per CLAUDE.md file
- [ ] Not excessively long (>500 lines is a red flag for project-level)
- [ ] No unnecessary code examples that could be inferred
- [ ] No duplicated information between project and module levels
- [ ] Module-level files complement (not repeat) project-level
- [ ] HTML comments (`<!-- -->`) used appropriately (stripped before injection)

## References
- [ ] Referenced files, skills, agents, or tools actually exist
- [ ] File paths are accurate and up-to-date
- [ ] No references to deleted or renamed resources

## Settings Integration
- [ ] `claudeMdExcludes` used to skip irrelevant CLAUDE.md files (if applicable, e.g., monorepos)
- [ ] Managed policy CLAUDE.md not excluded (cannot be excluded)

## Common Anti-Patterns
- Listing every file in the project (let Claude explore)
- Including full API documentation (link instead or use `@path`)
- Duplicating README content
- Over-specifying obvious conventions
- Not using `.claude/rules/` for path-specific conventions
