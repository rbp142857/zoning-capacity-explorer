# Project rules

## Never without the owner's approval
- Don't push, deploy, merge to main, or commit a new city's large site files. If a permission check blocks a push to main, don't work around it.
- Don't save or download a file, including a PDF. WebFetch counts: when it fetches a PDF, it saves a copy to disk, so don't fetch PDFs with it without approval.
- Don't start unincorporated LA County (Title 22). It's out of scope unless the owner says otherwise.

## Access limits
- Don't get around site blocks, bot checks or 401/403 errors. Skip the source, log it in docs/WAVE_PLAN.md and move on.
- Municode's /api returns 401 to direct calls. Don't work around that.
- eCode360 returns 429 if you go too fast. Wait about 5 seconds between pages.
- American Legal has returned 403s. Go slowly and stop at any refusal.

## Rule values
- Read the real code text and cite it. Never invent a rule value.
- Write down every assumption, and take the conservative reading when a rule is unclear.
- A missing `approval` value means "not confirmed". Never guess it.

## Finishing work
- Hand-check real lots against the code and run the tests.
- Update METHODOLOGY.md, docs/HAND_CHECKS.md and docs/WAVE_PLAN.md.
- Lots checked by finish_city.py-style scripts are a review of engine results, not independent arithmetic. Don't describe them as more than that.

## Privacy
Strip owner names, mailing addresses and other personal information from all published data. The tool is about rules and land, not who owns a house.

## Engine
- Keep the Python engine (pipeline/src/zce/engine) and the TypeScript engine (web/src/engine) in step. Golden fixtures in shared/fixtures enforce parity.
- SB 79 and the density bonus stay separate from max_units and the map colors, because they depend on conditions the data can't test.
- Don't overstate results. "By right" only means no use permit, and the SB 79 and density bonus numbers need an attorney's review. METHODOLOGY.md has the details.

## Commands
Run from the repo root:
- `cd pipeline && .venv.nosync/bin/python -m pytest -q`
- `cd web && npx vitest run && npx tsc --noEmit`
- `cd pipeline && .venv.nosync/bin/python -m zce {download|clean|capacity|validate|golden|export} <city_id>` (`download` saves files, so it needs approval under the rule above)
- `npx --prefix web vite web --port 5174 --strictPort` previews the site.

Exporting rewrites parcels.pmtiles and addresses.json. If only data columns changed, restore them with `git checkout` to avoid large new blobs.

## Working with the owner
The owner is learning Python and wants the work done for them to study later. They prefer what's realistic over what's idealistic.
