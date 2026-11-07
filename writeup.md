# Week 7 Writeup — Agent Orchestration: The Recipe Box Sprint

**Name:** Parwana Babakarkhil
**Repository:** https://github.com/parwana-p/recipe-box-week7
**Orchestrator:** Google Antigravity Agent Manager. Each worktree was opened as its own project, with one conversation per agent.
**Models:** Claude Sonnet 4.6 (Thinking) for Part I and the first generator rounds. I switched to Gemini 3.8 Flash after Claude hit its quota (details below).

---

## Part I — Concurrent agents (Tasks 1 and 2)

### Worktree setup
```bash
git worktree add ../recipe-task-a -b task-a   # Agent A: Task 1, Shopping list
git worktree add ../recipe-task-b -b task-b   # Agent B: Task 2, Tag filter
```
Both worktrees started from the same commit (`9138281`). In Antigravity I added
`recipe-task-a` and `recipe-task-b` as two separate projects, sent Agent A its prompt and
switched immediately to send Agent B its prompt. Both conversations showed the "running"
spinner at the same time (screenshot taken at 23:56).

| | Agent A (`task-a`) | Agent B (`task-b`) |
|---|---|---|
| Task | `GET /shopping-list?ids=1,2,3`, merged and de-duplicated ingredients; 400 for malformed ids, 404 for unknown ids | `GET /recipes?tag=breakfast`; no tag returns all recipes as before |
| Result | 6 new tests, 9/9 passing | 3 new tests, all passing |
| Commit | `9b29f71` | `6a93a78` |

### How I kept them from colliding
- **Separate working directories:** each agent could only see and edit its own worktree, so
  they never wrote to the same file on disk at the same time.
- **Scoped prompts:** "Only work in this folder. Do not commit." I reviewed the results and
  made the commits myself, so neither agent could change history or another branch.
- **Independent tasks:** I picked two tasks that touch different endpoints.

### Collisions and risks observed
- `git merge task-a` was a **fast-forward**.
- `git merge task-b` **auto-merged `main.py`** (Agent A appended `/shopping-list` at the end;
  Agent B changed `list_recipes` in the middle), but hit a **conflict in `test_main.py`**:
  both agents appended their tests at the end of the same file. I resolved it by keeping
  both sides (merge commit `f76d71b`), then ran `pytest` to confirm the combined suite passed.
- **Lesson:** "independent" tasks are still not independent at the file level. Shared files
  like the single test file, `main.py`'s import line, or a shared README are where
  parallel agents collide. Splitting tests per feature (e.g. `tests/test_shopping_list.py`)
  would have avoided the conflict completely.
- **Other risk:** both worktrees share one `recipes.db` path relative to each folder, so they
  did not share data. Running one server for both could have mixed their test data.

---

## Part II — Generator–critic loop (Task 3, Ingredient scaling)

Setup: a third worktree (`git worktree add ../recipe-task-c -b task-c`) with **two
conversations in the same project**: *generator* (writes code) and *critic* (reviews it and
may only write to `reviews/`). Each critique is saved as a file and every step is its own
commit, so the loop is fully evidenced in the history of `task-c`.

**Rubric given to the critic:**
1. *Correctness:* decimals (`1.5 cups`), fractions (`1/2 tsp`), no number (`salt`), number
   without unit (`3 eggs`), invalid factor (0, negative, missing) → 400/422, unknown id → 404.
2. *Tests:* each case above is covered by a behavioral test.
3. *Clarity:* readable code, clear helper names, no duplicated logic.

### Transcript (summarized; full reviews in `reviews/critique-round-{1,2,3}.md`)

| Step | Commit | Who | What happened |
|---|---|---|---|
| Round 0 | `e13fc07` | Generator (Claude) | Added `GET /recipes/{id}/scaled?factor=`, a `_QTY_RE` regex and `_scale_ingredient`, plus tests. |
| Critique 1 | `0db7173` | Critic (Claude) | **VERDICT: REVISE.** ❌ *Blocking:* the regex `^(\d+(?:\.\d+)?)` missed fractions, so `"1/2 tsp salt"` was silently returned unscaled (the critic verified it by running the regex). ❌ *Blocking:* no fraction test. ⚠️ *Minor:* `"3 eggs"` was only covered inside a batch test. ✅ 422 for invalid factor is allowed by the rubric. |
| Revision 1 | `aea4a44` | Generator (Claude) | Regex now `^(\d+(?:[./]\d+)?)`; new `_parse_quantity` helper does `num/denom`; added `test_scaled_fraction_quantity` and `test_scaled_number_without_unit`. |
| Critique 2 | `6010569` | Critic (Gemini) | Confirmed all three round-1 problems **FIXED**, then found a **new** gap: no test for a **negative factor**, which rubric item 1 lists. **VERDICT: REVISE.** |
| Revision 2 | `cc41659` | Generator (Gemini) | Added `test_scaled_factor_negative_422`; 22/22 tests passing. |
| Critique 3 | `fafa770` | Critic (Gemini) | Every case mapped to a dedicated test; Correctness, Tests and Clarity all PASS. **VERDICT: ACCEPT.** |

Result: **two revision rounds** before sign-off.

**Model switch:** critique round 2 first failed with an Antigravity quota error on Claude
Sonnet. I re-ran it with Gemini 3.8 Flash, and kept Gemini for the rest of the loop. A side
effect was that the critic was a *different model* from the one that wrote rounds 0–1,
which makes the review more independent.

### What the critic still missed (my own review after ACCEPT)
- `"1/0 cup"` would raise `ZeroDivisionError` in `_parse_quantity` and return a **500**.
- Mixed numbers like `"1 1/2 cups"` are scaled wrongly: the regex takes only the leading `1`,
  so factor 2 gives `"2 1/2 cups"` instead of `"3 cups"`.

Neither case was in the rubric, so the critic was correct by its own criteria. The loop
can only be as good as the rubric it checks against.

---

## Autonomy and supervision

| Agent | Allowed | Not allowed | How I supervised |
|---|---|---|---|
| Agent A / Agent B (Part I) | Read and edit files in its own worktree, run `pytest` (Turbo mode: commands ran without asking) | Committing, touching other folders | Isolated by worktree; I read each summary, re-ran `pytest`, committed, merged and resolved the conflict myself |
| Generator (Part II) | Edit `main.py` and `test_main.py`, run `pytest` | Editing `reviews/`, committing | Only acted on the critic's written review; I committed after each round |
| Critic (Part II) | Read code, run checks, write `reviews/critique-round-N.md` | Modifying `main.py` or `test_main.py` | Fixed rubric; verdict had to be REVISE or ACCEPT; I checked each review file in git |

Turbo mode was a deliberate trade-off. It made two agents running at once practical (no
permission prompts to answer in two places), and the risk was contained because each agent
worked in a disposable worktree and could not commit. I would not use Turbo on a main checkout.

---

## What I learned

Running two agents at once was easy; the real work was choosing tasks and boundaries so
their results could be merged. Even with separate worktrees, they collided in the one file
they both appended to. Worktrees prevent agents from overwriting each other's files while
they work, but not from conflicting at merge time, so I still need to review the merge myself.
The generator–critic loop worked well: the critic found a real silent bug (unscaled
fractions) and a real test gap that the generator had called "done". But it only checks
what the rubric lists, as the division-by-zero and mixed-number cases show. A loop with
written reviews and one commit per round also gave me an audit trail for free.
