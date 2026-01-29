# Running Mutation Testing in Docker

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up -d
docker-compose exec mutation-testing bash
```

This will start the container and give you a bash shell to run your own scripts.

### Option 2: Direct Docker

```bash
docker build -t fastapi-mutation-testing .
docker run -it -v $(pwd):/app fastapi-mutation-testing
```

## Inside the Container

Once in the container bash shell, you can run:

```bash
# Run your custom mutation testing script
python your_custom_script.py

# Or run the provided mutation script
python mutationscript.py --run-tests

# Or run pytest directly
pytest tests/
```

## What Gets Generated

Results will be saved to `mutation_output/` directory on your host machine (mounted from the container):

- `consolidated_mutations.diff` - All mutations with diffs
- `mutation_report.md` - Detailed analysis report
- `mutation_results.json` - Machine-readable results
- `tested_routines_source.py` - Source code of tested functions
- `ANALYSIS_SUMMARY.md` - Executive summary

## Will Results Differ Across Operating Systems?

**Short Answer:** Results should be identical (or nearly identical)

**Why:**

- ✅ Mutations are applied to source code (OS-independent)
- ✅ Python code being tested is cross-platform
- ✅ pytest test runner is cross-platform
- ✅ Line numbering is consistent across OSes

**Minor Exceptions:**

- File path separators (handled by pytest)
- Line endings (if git doesn't normalize CRLF/LF)
- Python version differences (we specify 3.12)

## Will Different Results Affect Your Report?

**No.** The consolidated diff and report files are **deterministic**:

- Same mutations generated every time
- Same test outcomes (KILLED/SURVIVED)
- Same statistics and analysis

**The results should be identical across all operating systems and runs** as long as:

1. Python 3.12 is used (specified in Dockerfile)
2. Same test suite and dependencies
3. Same source code version

## Running Manually (Without Docker)

If running locally:

```bash
pip install -e .
pip install pytest
python mutationscript.py --run-tests
```

Results will be identical to Docker runs on the same Python version.

## Troubleshooting

### Docker Daemon Not Running (Windows)

If you see: `The system cannot find the file specified` or similar Docker connection errors:

1. **Start Docker Desktop:**
   - Open Docker Desktop application
   - Wait for it to fully start (check system tray)
   - Try `docker-compose up -d` again

2. **Check Docker Status:**

   ```bash
   docker ps
   ```

   Should show your running containers (or empty list if none running)

3. **If Docker Desktop won't start:**
   - Restart your computer
   - Or run without Docker (see "Running Manually" section above)
