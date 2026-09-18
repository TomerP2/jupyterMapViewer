# Project notes for Claude

## Testing

After making any changes, run the test suite to catch regressions:

```bash
python3.11 -m pytest -v
```

Tests live in `tests/`. They exercise `map_viewer` end-to-end with a real GeoJSON and a real GeoTIFF (generated in-memory via fixtures), so they catch import errors, file-reading issues, and map construction failures.
