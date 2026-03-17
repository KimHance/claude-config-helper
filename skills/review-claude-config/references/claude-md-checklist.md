# CLAUDE.md Review Checklist

## File Discovery
- [ ] Project root `CLAUDE.md` exists
- [ ] Module-level `CLAUDE.md` files exist where appropriate (large subdirectories with distinct conventions)

## Structure
- [ ] Has clear sections (overview, conventions, commands, patterns, constraints)
- [ ] Uses headings for scanability
- [ ] Not a wall of text — structured with lists and short paragraphs

## Content Quality
- [ ] Uses imperative tone ("Use X", "Never do Y") — not descriptive ("This project uses X")
- [ ] Instructions are actionable and specific
- [ ] No vague guidance ("be careful", "use best practices")
- [ ] No stale or contradictory instructions
- [ ] No information Claude already knows (language basics, common patterns)

## Context Window Efficiency
- [ ] Not excessively long (>500 lines is a red flag for project-level)
- [ ] No unnecessary code examples that could be inferred
- [ ] No duplicated information between project and module levels
- [ ] Module-level files complement (not repeat) project-level

## References
- [ ] Referenced files, skills, agents, or tools actually exist
- [ ] File paths are accurate and up-to-date
- [ ] No references to deleted or renamed resources

## Common Anti-Patterns
- Listing every file in the project (let Claude explore)
- Including full API documentation (link instead)
- Duplicating README content
- Over-specifying obvious conventions
