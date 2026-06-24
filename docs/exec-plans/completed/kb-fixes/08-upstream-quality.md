# 08 — Surface Upstream Extraction Quality at Build Time

## Problem

The KB build completes normally even when the extraction set is visibly noisy. Users see "Done" and may assume the KB is production-ready. The build result does not communicate that the root issue is upstream extraction quality.

## Steps

1. At the start of the KB build, scan all `extractions/*.json` for quality signals:
   - Count sources with `quality.flags` non-empty.
   - Count sources with `quality.text_coverage` below 0.5.
   - Count sources with zero entities.

2. Emit a structured pre-build quality report:
   ```
   Extraction quality summary:
     15 sources total
      3 with low entity count
      1 with low text coverage
      0 failed extractions
   ```

3. At the end of the build, if any quality issues were found, emit a clear closing warning:
   ```
   KB build completed with warnings.
   Cause: 4 of 15 sources have low-quality extractions.
   Recommendation: re-run /extract with --force on flagged sources before distributing this KB.
   ```

4. Write the quality summary to `kb/build-report.json` so agents can read it programmatically:
   ```json
   {
     "build_date": "2026-06-24T10:00:00Z",
     "sources_total": 15,
     "sources_with_warnings": 4,
     "overall_quality": "warning",
     "recommendation": "Re-extract flagged sources."
   }
   ```

5. Add acceptance tests:
   - Build from clean extractions → `overall_quality: ok`, no closing warning.
   - Build from 30%-noisy extractions → closing warning printed, `overall_quality: warning`.

## Acceptance criteria

- Pre-build quality summary is printed every time.
- Closing warning is printed when upstream quality is below threshold.
- `kb/build-report.json` is written after every build.
- "Done" output alone is never the only signal when quality is degraded.
