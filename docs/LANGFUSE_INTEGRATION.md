# Langfuse Integration Guide

This document explains how Langfuse observability is integrated into the receipt inspection agent.

## Overview

The project **requires** Langfuse for:
- Distributed tracing of agent operations
- Token usage tracking
- Performance monitoring
- Dataset management for evaluations

**Important**: Example scripts will exit with a clear error message if Langfuse is not available. This fail-fast approach ensures consistent observability in development and makes issues immediately visible.

## Architecture

### Fail-Fast Validation Pattern

All example scripts use a startup check that validates Langfuse availability before running:

```python
from agent_sdk.utils.langfuse_check import require_langfuse

async def main():
    # This will exit if Langfuse is not available
    require_langfuse()

    # Rest of your code runs with guaranteed Langfuse availability
    agent = ReceiptInspectionAgent(config=config)
    # ...
```

### How It Works

The `require_langfuse()` function performs two checks:

1. **Credentials Check**: Verifies `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are configured
2. **Service Check**: Verifies Langfuse service is reachable via HTTP

If either check fails, the script exits immediately with a helpful error message explaining how to fix the issue.

## Availability Checks

### Successful Check

Langfuse is considered **available** when:

✅ Environment variables are set (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`)
✅ Langfuse service responds to HTTP requests at `LANGFUSE_HOST`

Script proceeds normally and captures traces.

### Failed Check: Missing Credentials

```
❌ Langfuse credentials not configured!

This example requires Langfuse for tracing and observability.

Setup instructions:
1. Copy .env.example to .env
2. Start Langfuse: docker compose up -d
3. Visit http://localhost:3000 and create account
4. Go to Settings → API Keys
5. Copy your keys to .env:
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
```

### Failed Check: Service Unreachable

```
❌ Langfuse service not reachable at http://localhost:3000!

Error: URLError: <urlopen error [Errno 61] Connection refused>

This example requires Langfuse to be running.

To start Langfuse:
1. Run: docker compose up -d
2. Wait ~30 seconds for services to start
3. Verify: curl http://localhost:3000
4. Check logs: docker compose logs -f langfuse-web

Then run this script again.
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxx
LANGFUSE_HOST=http://localhost:3000
```

Get these from:
1. Start Langfuse: `docker compose up -d`
2. Visit http://localhost:3000
3. Create account and project
4. Go to Settings → API Keys
5. Copy keys to `.env`

**Important**: If you have a `LANGFUSE_HOST` environment variable set in your shell, it will override the `.env` file value. See [Troubleshooting](#troubleshooting) below.

### Docker Compose

Langfuse services defined in `docker-compose.yml`:
- `langfuse-db` - PostgreSQL database (port 5435 → 5432)
- `langfuse-clickhouse` - ClickHouse analytics (disabled on macOS for compatibility)
- `langfuse-redis` - Redis cache (port 6380 → 6379)
- `langfuse-web` - Web UI (port 3000 → 3000)
- `langfuse-worker` - Background worker

**Port Mapping**: The web service runs on port 3000 inside the container and is exposed on port 3000 on the host.

**Important**: Update passwords in `docker-compose.yml` before production use (see `# CHANGEME` comments).

## Starting Langfuse

```bash
# Start all services
docker compose up -d

# Wait for services to be ready (check logs)
docker compose logs -f langfuse-web
# Wait for "Ready" message (~30 seconds)

# Verify Langfuse is responding
curl http://localhost:3000
# Should return HTTP 200

# Access the UI
open http://localhost:3000
```

## Integration Points

### Agent Code

The agent uses Langfuse decorators directly:

```python
from langfuse.decorators import langfuse_context, observe

@observe(name="extract_receipt_details")
async def extract_receipt_details(self, image_path, receipt_id):
    # Update trace with metadata
    langfuse_context.update_current_trace(
        name="receipt_inspection",
        metadata={"receipt_id": receipt_id, "image_path": image_path}
    )

    # ... extraction logic ...

    # Track token usage
    langfuse_context.update_current_observation(
        usage={
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens
        }
    )
```

### Example Scripts

All example scripts use the same pattern:

```python
from agent_sdk.utils.langfuse_check import require_langfuse

async def main():
    """Run receipt inspection example."""
    # Require Langfuse to be available
    require_langfuse()

    # Rest of your code...
```

Scripts that use this pattern:
- `examples/run_receipt_inspection.py`
- `examples/run_receipt_evaluation.py`
- `examples/setup_langfuse_dataset.py`

### Dataset Management

The `LangfuseDatasetManager` class provides:

```python
from agent_sdk.utils.langfuse_datasets import setup_receipt_inspection_dataset

# Create dataset from test cases
dataset_id = setup_receipt_inspection_dataset()
```

This creates a versioned dataset in Langfuse for tracking evaluation runs.

## Troubleshooting

### Issue: Wrong Port or Host Configuration

**Symptoms**: Script fails with "Langfuse service not reachable at http://localhost:XXXX"

**Diagnosis**: Incorrect LANGFUSE_HOST configuration

**Solution**:
```bash
# Check current configuration
echo $LANGFUSE_HOST
# Should be: http://localhost:3000

# Check if environment variable is overriding .env
# If set incorrectly, either:

# Option 1: Update for current session
export LANGFUSE_HOST=http://localhost:3000

# Option 2: Unset the environment variable (use .env value)
unset LANGFUSE_HOST

# Option 3: Update your shell profile (~/.bashrc, ~/.zshrc)
# Remove or update any incorrect LANGFUSE_HOST exports

# Verify .env file has correct value
cat .env | grep LANGFUSE_HOST
# Should show: LANGFUSE_HOST=http://localhost:3000
```

**Root cause**: Environment variables take precedence over `.env` files in Pydantic settings. The correct port is 3000.

### Issue: "Connection refused"

**Diagnosis**: Langfuse is not running

**Solution**:
```bash
# Check if services are running
docker compose ps

# If not running, start them
docker compose up -d

# Wait and check logs
docker compose logs -f langfuse-web
# Wait for "Ready" message

# Verify accessibility
curl http://localhost:3000
```

### Issue: "Credentials not configured"

**Diagnosis**: Missing or incorrect API keys in `.env`

**Solution**:
1. Ensure `.env` file exists: `ls -la .env`
2. Ensure keys are set: `cat .env | grep LANGFUSE`
3. Visit http://localhost:3000 → Settings → API Keys
4. Copy the correct keys to `.env`
5. Restart your script

### Issue: No traces appearing in UI

**Possible causes**:
1. Wrong API keys in `.env`
2. Using wrong project in Langfuse UI
3. Keys don't match the project

**Solutions**:
1. Verify keys in `.env` match Langfuse UI
2. Check active project in Langfuse UI top navigation
3. Regenerate keys if needed and update `.env`

### Issue: Services fail to start

**Common causes**:
1. Port conflicts (3000, 5435, 6380, 8125, 9002)
2. Docker resource limits
3. Database initialization errors

**Solutions**:
```bash
# Check for port conflicts
lsof -i :3000
lsof -i :5435

# View detailed logs
docker compose logs

# Restart from clean state
docker compose down -v  # WARNING: Deletes all data
docker compose up -d
```

## Performance Impact

### Trace Collection Overhead
- **~50-100ms per trace** - includes network round-trip to Langfuse
- Async flushing doesn't block agent execution
- Batch uploading optimizes network usage

### Token Tracking
- **Zero overhead** - metadata already available from API responses
- Simple dictionary updates
- No additional API calls

## Development Workflow

### Daily Development

```bash
# Morning: Start Langfuse
docker compose up -d

# Work on agent code
# All example scripts automatically connect

# Evening: Stop Langfuse (optional)
docker compose stop
```

### Quick Iteration (Without Traces)

If you want to run agent code without Langfuse overhead during rapid iteration:

1. Comment out `require_langfuse()` in your test script
2. Remove `@observe` decorators temporarily
3. Run your code
4. Re-enable before committing

**Note**: Example scripts are designed to always use Langfuse for consistency.

## Best Practices

### Development
- ✅ Always start Langfuse before running examples
- ✅ Use Docker Compose for local Langfuse
- ✅ Check Langfuse UI regularly to debug traces
- ✅ Name traces meaningfully with metadata

### Production
- ✅ Use external Langfuse instance (not Docker Compose)
- ✅ Set `LANGFUSE_HOST` to your Langfuse URL
- ✅ Use proper secrets management for API keys
- ✅ Monitor Langfuse availability
- ✅ Set up alerts for Langfuse downtime
- ❌ Don't use fail-fast checks in production (use health checks instead)

### Testing
- ✅ Start Langfuse before running test suite
- ✅ Verify traces are captured for all test cases
- ✅ Use Langfuse datasets for regression testing

## Production Deployment

For production environments:

1. **Deploy Langfuse separately** (not with Docker Compose)
   - Use Langfuse Cloud, or
   - Deploy self-hosted Langfuse on Kubernetes/ECS

2. **Remove fail-fast checks** from production code
   - Use health checks and monitoring instead
   - Implement circuit breakers for Langfuse failures
   - Consider graceful degradation pattern

3. **Configure proper secrets**
   - Use AWS Secrets Manager, HashiCorp Vault, etc.
   - Rotate keys regularly
   - Use separate keys per environment

4. **Monitor observability pipeline**
   - Track Langfuse trace success rate
   - Alert on Langfuse downtime
   - Monitor trace upload latency

## Related Documentation

- [docs/TESTING_GUIDE.md](TESTING_GUIDE.md) - Full testing instructions
- [docs/IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) - Technical architecture
- [Langfuse Documentation](https://langfuse.com/docs) - Official Langfuse docs
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python) - SDK documentation

## Summary

Langfuse integration in this project is:
- **Required**: Example scripts validate availability before running
- **Fail-fast**: Issues are caught immediately with helpful error messages
- **Production-ready**: Full observability with proper monitoring
- **Flexible**: Can be adapted for graceful degradation in production

The fail-fast pattern ensures **zero surprises** - if Langfuse isn't working, you know immediately.
