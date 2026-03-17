# Subagent Definitions Review Checklist

## Frontmatter
- [ ] Has `name` field
- [ ] Has `description` field with trigger examples
- [ ] Has `model` field with appropriate choice
- [ ] Description includes `<example>` blocks for accurate matching

## Model Selection
- [ ] `opus` — used for complex reasoning, deep analysis, creative tasks
- [ ] `sonnet` — used for standard tasks, code generation, structured output
- [ ] `haiku` — used for lightweight, fast, simple tasks
- [ ] `inherit` — used when the parent model choice should carry through
- [ ] Model choice is justified for the agent's workload

## Role Definition
- [ ] Clear statement of what the agent does
- [ ] Specific behavioral instructions
- [ ] Structured output format defined (if applicable)
- [ ] Step-by-step workflow outlined

## Scope
- [ ] Not overlapping with other agents' responsibilities
- [ ] Not too broad (trying to do everything)
- [ ] Not too narrow (could be a simple prompt instead)

## Tool Access
- [ ] If agent needs specific tools, they are mentioned in the instructions
- [ ] No unnecessary tool access requested
