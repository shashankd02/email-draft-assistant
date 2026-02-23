## Summary
- What changed:
- Why it changed:

## Scope
- [ ] Backend
- [ ] Frontend
- [ ] Database migration
- [ ] CI/Workflow
- [ ] Docs

## Validation
- [ ] `python -m compileall backend/src`
- [ ] `pytest -q` (backend)
- [ ] `npm run lint` (frontend)
- [ ] `npm run build` (frontend)
- [ ] Manual smoke test completed (login -> compose -> draft)

## Risk Review
- [ ] Auth/access boundaries reviewed
- [ ] Agent safety/intent guard behavior reviewed
- [ ] User-facing errors are friendly (no raw stack traces/provider internals)
- [ ] Breaking changes documented

## Deployment Notes
- [ ] Alembic migration included (if schema changed)
- [ ] Env/config updates documented
