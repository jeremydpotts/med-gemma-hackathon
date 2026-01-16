# Workflow Requirements - Med-Gemma Hackathon

**Purpose:** Standardize development practices and ensure quality throughout the competition
**Last Updated:** January 17, 2026 (Day 7)

---

## Critical Workflow Rules

### 1. Git Commit Protocol ⚠️ MANDATORY

**Commit After Every Session:**
- ✅ **REQUIRED:** Create a git commit after completing each think tank session
- ✅ **REQUIRED:** Create a git commit after completing each development milestone
- ✅ **REQUIRED:** Create a git commit at end of each day

**Commit Message Standards:**

```bash
# Session Commits (Brainstorming Phase)
git commit -m "Complete Session [N]: [Session Name]

[Brief description of outcomes]

Key decisions:
- [Decision 1]
- [Decision 2]
- [Decision 3]

[Additional details]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

```bash
# Development Commits (Implementation Phase)
git commit -m "[Component/Feature]: [Action taken]

[Details of what was implemented/fixed/improved]

- Changes made
- Files affected
- Tests added/updated
- Documentation updated

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Commit Frequency:**
- Minimum: After each completed session or milestone
- Recommended: Every 2-3 hours during active development
- Critical: Before testing anything risky or experimental
- Final: Before submission (with comprehensive commit message)

**What to Commit:**
- ✅ All session documents and summaries
- ✅ Code changes and new features
- ✅ Documentation updates
- ✅ Configuration files
- ✅ Test files and results
- ✅ Notebooks with outputs cleared (for size)
- ❌ Large datasets (use .gitignore)
- ❌ Model weights/checkpoints (use .gitignore)
- ❌ Temporary files
- ❌ Any files containing PHI (Protected Health Information)

---

### 2. Documentation Requirements

**Update After Every Session:**
1. **Session document** - Complete transcript with outcomes
2. **Session summary** - Executive summary (if major session)
3. **Progress log** - Update PROGRESS_LOG.md with day's work
4. **Todo list** - Mark completed items, add new items

**Required Documentation Files:**

| File | Update Frequency | Purpose |
|------|------------------|---------|
| `PROGRESS_LOG.md` | Daily | Track daily accomplishments and decisions |
| `SESSION_[N]_*.md` | Per session | Full session transcripts |
| `SESSION_[N]_SUMMARY.md` | Major sessions | Executive summaries |
| `README.md` | Weekly | Keep project overview current |
| `QUALITY_SCORING_FRAMEWORK.md` | Weekly | Update scores at checkpoints |

---

### 3. Quality Checkpoints

**Evaluate Quality Score After:**
- ✅ Each major session (Sessions 1, 4, 5)
- ✅ Prototype completion (Day 13)
- ✅ Feature complete (Day 17)
- ✅ Advanced features done (Day 21)
- ✅ Testing complete (Day 25)
- ✅ Final polish done (Day 32)
- ✅ Pre-submission (Day 36)

**Score Thresholds:**
- **AA+ Grade:** ≥90/100 in each category (270/300 total)
- **Action Required:** If any category <80/100
- **Escalation:** If overall <85/100

---

### 4. Session Completion Checklist

After completing ANY think tank session:

**Immediate (Within Session):**
- [ ] Complete session document with all expert contributions
- [ ] Record key decisions and consensus points
- [ ] Document action items for next session
- [ ] Update quality scores if applicable

**Post-Session (Within 30 minutes):**
- [ ] Create session summary (for major sessions)
- [ ] Update todo list (mark completed, add new)
- [ ] Update PROGRESS_LOG.md with session outcomes
- [ ] **Commit to git with detailed commit message** ⚠️ REQUIRED
- [ ] Push to GitHub (backup)

**Verification:**
- [ ] All files added to git (`git status` shows clean)
- [ ] Commit message includes session outcomes
- [ ] Co-authored-by tag included
- [ ] Session marked complete in todo list

---

### 5. Development Milestone Checklist

After completing ANY development milestone:

**Code Quality:**
- [ ] Code follows PEP 8 (Python) or style guide
- [ ] All functions have docstrings
- [ ] No hardcoded secrets or credentials
- [ ] No PHI in code or comments
- [ ] Error handling implemented
- [ ] Input validation added

**Testing:**
- [ ] Unit tests written for new functions
- [ ] Tests pass locally
- [ ] Edge cases tested
- [ ] Performance acceptable

**Documentation:**
- [ ] Code comments for complex logic
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Architecture docs updated

**Git:**
- [ ] **Commit changes with clear message** ⚠️ REQUIRED
- [ ] Push to GitHub
- [ ] Tag major milestones (e.g., `v0.1-prototype`)

---

### 6. Daily Workflow

**Start of Day:**
1. Review yesterday's progress log
2. Check todo list for today's tasks
3. Pull latest changes: `git pull origin main`
4. Review quality scores and priorities

**During Day:**
1. Work on prioritized tasks
2. Document as you go (comments, notes)
3. Test incrementally (don't batch testing)
4. Commit frequently (every 2-3 hours)

**End of Day:**
1. Update PROGRESS_LOG.md with accomplishments
2. Update todo list (completed + new items)
3. **Create end-of-day commit** ⚠️ REQUIRED
4. Push to GitHub
5. Review tomorrow's priorities

---

### 7. HIPAA Compliance Checklist

**Before EVERY Commit:**
- [ ] No real patient data (PHI) in files
- [ ] No names, dates, identifiers in test data
- [ ] DICOM files de-identified (if any)
- [ ] Sample data clearly marked as synthetic
- [ ] .gitignore blocks PHI file patterns

**Before EVERY Session:**
- [ ] Using only de-identified public datasets
- [ ] No PHI in discussion or examples
- [ ] Security measures documented

---

### 8. Submission Preparation Checklist

**5 Days Before Deadline (Day 32):**
- [ ] All code committed and pushed
- [ ] Documentation complete
- [ ] Demo video recorded
- [ ] Quality audit passed (≥90/100)

**3 Days Before Deadline (Day 34):**
- [ ] Final testing complete
- [ ] Submission notebook validated
- [ ] All materials organized in `submission/`
- [ ] Backup created

**1 Day Before Submission (Day 36):**
- [ ] Internal review passed
- [ ] Security audit complete
- [ ] Final commit with submission tag
- [ ] **Comprehensive final commit message**

**Submission Day (Day 37 - Feb 19):**
- [ ] Submit to Kaggle
- [ ] Verify submission accepted
- [ ] Create final backup
- [ ] **Celebratory commit!**

---

### 9. Emergency Protocols

**If Git Commit Fails:**
1. Check git status: `git status`
2. Verify all files added: `git add -A`
3. Check for conflicts: `git diff`
4. Force commit if needed: Document why in message
5. Create manual backup if git issues persist

**If Quality Score Drops Below Threshold:**
1. Immediate assessment of gaps
2. Create remediation plan
3. Allocate contingency time
4. Re-evaluate scope if needed
5. Document decisions in emergency log

**If Behind Schedule:**
1. Review feature priorities
2. Consider scope reduction
3. Focus on core features (2D baseline)
4. Document tradeoffs
5. Ensure minimum viable product (MVP) complete

---

### 10. Best Practices

**Code Development:**
- Write tests BEFORE implementation (TDD)
- Commit working code, not broken code
- Use feature branches for risky changes
- Keep main branch always deployable

**Documentation:**
- Document WHY, not just WHAT
- Update docs when code changes
- Keep README accurate
- Use clear, concise language

**Communication:**
- Clear commit messages (future you will thank you)
- Document decisions and rationale
- Track action items and owners
- Celebrate wins!

**Time Management:**
- Feature freeze Day 17 (STRICT)
- Buffer days for unexpected issues
- Quality over quantity
- Don't over-engineer

---

## Workflow Automation Scripts

### Auto-Commit Script (Optional)

```bash
#!/bin/bash
# auto-commit.sh - Helper for standardized commits

echo "Enter commit type (session/feature/docs/fix):"
read TYPE

echo "Enter brief description:"
read DESC

echo "Enter details (optional, press Enter to skip):"
read DETAILS

if [ "$DETAILS" = "" ]; then
    DETAILS="No additional details"
fi

git add -A
git commit -m "$TYPE: $DESC

$DETAILS

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo "✅ Committed! Push to remote? (y/n)"
read PUSH

if [ "$PUSH" = "y" ]; then
    git push origin main
    echo "✅ Pushed to GitHub!"
fi
```

### Session Complete Script

```bash
#!/bin/bash
# session-complete.sh - Run after completing a session

SESSION_NUM=$1
SESSION_NAME=$2

echo "📝 Session $SESSION_NUM: $SESSION_NAME - Completion Protocol"
echo ""

# Update todo list
echo "✓ Mark session as complete in todo list"

# Commit changes
echo "✓ Committing changes..."
git add -A
git commit -m "Complete Session $SESSION_NUM: $SESSION_NAME

Session outcomes documented and committed.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push origin main

echo ""
echo "✅ Session $SESSION_NUM complete and committed!"
echo "📊 Next: Review session outcomes and prepare for next session"
```

---

## Compliance Verification

**Use this checklist before EVERY submission:**

### Git Compliance:
- [ ] All sessions committed
- [ ] All milestones committed
- [ ] Commit messages follow standard
- [ ] Co-authored-by tags present
- [ ] No PHI in git history

### Documentation Compliance:
- [ ] All session docs complete
- [ ] Progress log updated
- [ ] Quality scores current
- [ ] README accurate

### Quality Compliance:
- [ ] Overall score ≥90/100
- [ ] All categories ≥80/100
- [ ] Critical requirements met
- [ ] Security audit passed

### Submission Compliance:
- [ ] Submitted 5 days early (Feb 19)
- [ ] All materials included
- [ ] Submission notebook validated
- [ ] Backup created

---

## Summary: Critical Requirements

**MUST DO After Every Session:**
1. ✅ Complete session document
2. ✅ Update todo list
3. ✅ Update progress log
4. ✅ **COMMIT TO GIT** ⚠️ REQUIRED
5. ✅ Push to GitHub

**MUST DO Before Submission:**
1. ✅ Quality audit (≥90/100)
2. ✅ Security audit (no PHI)
3. ✅ Documentation complete
4. ✅ All code committed
5. ✅ Submission validated

---

**Remember:** Commit early, commit often, commit after sessions!

**Git is your safety net.** Use it religiously.

---

**Last Updated:** January 17, 2026
**Next Review:** Day 10 (after Session 5)
