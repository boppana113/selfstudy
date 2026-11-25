# 2026-11-24 · ownership · build session 1

**Built (in `~/llm-gateway`, commit 5306c79):** steps 1–3 of `docs/stage-1-config.md`.
- Flat config types: `Config { projects, users, api_keys, providers }` as `Vec`s; `Project.user_ids: Vec<u32>` (user chose many-to-many); `ApiKey { key, project_id, user_id: Option<u32>, providers: Vec<String> }`; `ProviderConfig` with a `ProviderId` enum (ahead of stage 2).
- `Config::from_toml` / `Config::load` + `config.example.toml`.
- `find_key` as a loop, then `iter().find(..)`. 4 tests passing.

**Design detours:** first copied Pydantic's nested HashMap layout; switched back to flat `Vec`s for the borrowing reps (HashMap index is the stretch). Rule learned: one owner holds the data, everything else points at it by id (`project_id`, `user_ids`, provider names).

**Errors hit:**
- E0063: `Option` fields still must be written (`None`).
- E0382 (partial move): `vec![anthropic_config.name]` moved one field out, then the whole struct couldn't move. Fixed with `.clone()`. Initially said it "consumed the object"; corrected to partial move.
- E0507: `Option<ApiKey>` return + `*k` → can't move out of a borrow. User: "we'd end up removing the key from the config."
- E0502: hold `k`, then `push`. User predicted the line and the reallocation; corrected "bad dealloc at end" → dangling pointer / use-after-free. Fixed by using `k` before the push (borrow ends at last use).
- Path passed to `from_toml` (both `&str`) → parse panic. Lesson: text vs path; newtypes later.

**Mental model (own words):** Config owns every key; find_key returns a borrow; while I hold it I can't modify config. Missing "because": a mutation could move/free what the reference points to.

**Open:** `Some` wrapping (thought `Some` wraps both cases); `.` vs `::` for associated fns.

**Next:** Step 4 (`project_for`, `allows`, Debug redaction, E0106), then Step 5 (`main check`).
