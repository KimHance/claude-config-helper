# Memory System Review Checklist

## MEMORY.md Index
- [ ] `MEMORY.md` exists in the memory directory
- [ ] Under 200 lines (truncation risk beyond that)
- [ ] Contains only links to memory files with brief descriptions
- [ ] No memory content directly in MEMORY.md (it's an index, not a memory)
- [ ] Links point to files that actually exist

## Memory Files
- [ ] Each file has proper frontmatter: `name`, `description`, `type`
- [ ] `type` is one of: `user`, `feedback`, `project`, `reference`
- [ ] `description` is specific enough for relevance matching in future conversations
- [ ] File naming is semantic (by topic, not chronological)

## Content Quality
- [ ] No duplicate memories covering the same topic
- [ ] No contradictory memories
- [ ] Feedback memories include **Why:** and **How to apply:** lines
- [ ] Project memories include **Why:** and **How to apply:** lines
- [ ] No relative dates ("next Thursday") — should be absolute ("2026-03-20")
- [ ] No stale project memories (check dates against current date)

## What Should NOT Be in Memory
- [ ] No code patterns derivable from the codebase
- [ ] No git history information (use git log)
- [ ] No debugging solutions (the fix is in the code)
- [ ] No content already in CLAUDE.md files
- [ ] No ephemeral task details
