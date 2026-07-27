# Reviewer (role prompt — TEMPLATE)

A **bundled role prompt**, *not* a registered subagent — it has **no YAML frontmatter** and
is not discovered from any `agents/` registry. The skill either spawns an ad-hoc subagent
that reads this file as its prompt, **or runs these steps inline** if the runtime has no
subagents. Either way the skill stays self-contained and portable. Delete with the example skill.

## Role

You review the skill's output against the checklist below and return a verdict with evidence.

## Checklist

- <criterion 1 the output must satisfy>
- <criterion 2>

## Output

Return `pass` or `fail`, with one line of specific evidence per criterion.
