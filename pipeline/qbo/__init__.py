"""QuickBooks Online sandbox handoff. Runs only from `ctl qbo-auth` and `ctl qbo-post`, never in
`ctl build` or CI. The close in `data/out/close.json` is the source of truth, QuickBooks is a
destination."""
