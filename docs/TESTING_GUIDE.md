# Testing Guide

This guide walks you through testing the receipt inspection agent after the recent updates.

## Prerequisites

Before testing, ensure you have:

1. ✅ **Langfuse Running**
   ```bash
   docker compose up -d
   # Wait 2-3 minutes for services to start
   docker compose logs -f langfuse-web
   # Look for "Ready" message
   ```

2. ✅ **Environment Variables Configured**
   - Copy `.env.example` to `.env`
   - Add your `ANTHROPIC_API_KEY`
   - Add your `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` from Langfuse UI (http://localhost:3000)

3. ✅ **Dependencies Installed**
   ```bash
   uv pip install -e ".[dev]"
   # or
   uv sync --all-extras
   ```

## Testing Steps

### Step 1: Verify Langfuse Connection

Visit http://localhost:3000 and ensure:
- You can log in
- Your project is created
- API keys are available in Settings → API Keys

### Step 2: Set Up Langfuse Dataset

```bash
python examples/setup_langfuse_dataset.py
```

**Expected Output**:
```
Setting up Langfuse Dataset

Creating dataset from test cases...
Created new dataset: receipt_inspection_v1
  Added item: rec_walmart_supplies
  Added item: rec_shell_gas
  ... (10 items total)

✓ Dataset created successfully!
Dataset ID: receipt_inspection_v1

→ View dataset in Langfuse: http://localhost:3000
   Navigate to: Datasets → receipt_inspection_v1
```

**Verification**:
1. Go to http://localhost:3000
2. Navigate to "Datasets"
3. You should see "receipt_inspection_v1" with 20 items

### Step 3: Receipt Images (Already Included!)

✅ **Good news**: If you've downloaded the Roboflow dataset, the images are already in place!

**Dataset Location**:
```
data/
├── test/images/      # 20 test images (USED FOR EVALUATION)
├── train/images/     # 144 training images
└── valid/images/     # Validation images
```

The test cases in `data/datasets/receipt_test_cases.json` reference the 20 images in `data/test/images/`.

**Image Types in Test Set**:
- 12 Gas station receipts (travel-related)
- 3 Nissan dealership/service receipts (not travel-related)
- 1 Retail store receipt (not travel-related)
- 2 Sequoia location receipts (not travel-related)
- 2 Tundra location receipts (not travel-related)

All images are in JPEG format with Roboflow naming:
```
Gas_20240605_164059_Raven_Scan_3_jpeg.rf.hash.jpg
```

**If You Need the Dataset**:
1. Visit https://universe.roboflow.com/newreceipts/receipt-handwriting-detection
2. Create a free Roboflow account
3. Download the dataset (JPEG format recommended)
4. Extract to the project root so you have `data/train/`, `data/test/`, `data/valid/`

### Step 4: Test Single Receipt Processing

**Without Images** (will fail gracefully):
```bash
python examples/run_receipt_inspection.py
```

**Expected Output**:
```
Error: Image file not found: data/images/walmart_supplies.jpg
Note: This example requires actual receipt images.
See data/datasets/receipt_test_cases.json for test case structure.
```

**With Images**:
```bash
python examples/run_receipt_inspection.py
```

**Expected Output**:
```
Receipt Inspection Agent Demo

Processing receipt image: data/images/walmart_supplies.jpg

Step 1: Extracting receipt details...
Receipt details extracted successfully!

Extracted Details:
{
  "receipt_id": "example_001",
  "merchant": "Walmart",
  "location": {
    "city": "Vista",
    "state": "CA",
    "zipcode": "92083"
  },
  ...
}

Step 2: Evaluating for audit...
Audit evaluation complete!

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Criterion                    ┃ Result ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Not Travel Related           │ ✓      │
│ Amount Over $50              │ ✓      │
│ Math Error                   │ ✗      │
│ Handwritten X                │ ✗      │
│ Needs Audit                  │ YES    │
└─────────────────────────────┴────────┘

✓ Receipt inspection complete!
→ View traces in Langfuse: http://localhost:3000
```

**Verification**:
1. Go to http://localhost:3000
2. Navigate to "Traces"
3. Find the "receipt_inspection" trace
4. Verify you see:
   - Token usage
   - Input (image) and output (structured data)
   - Nested observations for extraction and audit

### Step 5: Run Full Evaluation Suite

**Without Images**:
```bash
python examples/run_receipt_evaluation.py
```

**Expected Output**:
```
Receipt Inspection Evaluation

Loaded 10 test cases
Langfuse dataset integration enabled

Running evaluations...

⚠ Image not found: data/images/walmart_supplies.jpg
... (repeated for all images)

Evaluation Summary

Overall Results
┏━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Value ┃
┡━━━━━━━━━━━━╇━━━━━━━┩
│ Total Cases │ 10    │
│ Passed      │ 0     │
│ Failed      │ 10    │
│ Pass Rate   │ 0.0%  │
└─────────────┴───────┘

Failed Cases (10):
...
```

**With Images**:
```bash
python examples/run_receipt_evaluation.py
```

**Expected Output**:
```
Receipt Inspection Evaluation

Loaded 10 test cases
Langfuse dataset integration enabled

Running evaluations...

Evaluating rec_walmart_supplies...
✓ rec_walmart_supplies

Evaluating rec_shell_gas...
✓ rec_shell_gas

... (continues for all 10 test cases)

Evaluation Summary

Overall Results
┏━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Value ┃
┡━━━━━━━━━━━━╇━━━━━━━┩
│ Total Cases │ 10    │
│ Passed      │ 8-10  │  (depends on Claude's performance)
│ Failed      │ 0-2   │
│ Pass Rate   │ 80-100%│
└─────────────┴───────┘

Metric Averages
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Metric                   ┃ Average Score ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ audit_decision_correct   │ 0.80-1.00     │
│ audit_criteria_accuracy  │ 0.85-0.95     │
│ extraction_accuracy      │ 0.75-0.90     │
└──────────────────────────┴───────────────┘

✓ Evaluation complete!
→ View detailed traces in Langfuse: http://localhost:3000

Results saved to: eval_results/receipt_eval_XXXXXXXX.json
```

**Verification**:
1. Check `eval_results/` directory for JSON results file
2. Go to http://localhost:3000
3. Navigate to "Traces" - you should see 10 traces (one per test case)
4. Navigate to "Datasets" → "receipt_inspection_v1" - traces should be linked to dataset items

### Step 6: Analyze Results in Langfuse

1. **View Individual Traces**:
   - Go to Traces in Langfuse UI
   - Click on any "receipt_inspection" trace
   - Examine:
     - Token usage (input/output tokens)
     - Latency
     - Nested observations (extract_receipt_details, evaluate_receipt_for_audit)
     - Input/output data

2. **Check Dataset Integration**:
   - Go to Datasets → receipt_inspection_v1
   - Click on any dataset item
   - You should see linked traces from evaluation runs

3. **Monitor Performance**:
   - Look for patterns in failures
   - Check which test cases consistently pass/fail
   - Examine token usage trends

## Troubleshooting

### Issue: "No module named 'agent_sdk'"

**Solution**:
```bash
pip install -e .
# or
uv pip install -e .
```

### Issue: "Langfuse API key error"

**Solution**:
1. Verify Langfuse is running: `docker compose ps`
2. Check `.env` file has correct keys
3. Verify keys in Langfuse UI (Settings → API Keys)
4. Make sure you're using the correct project

### Issue: "ANTHROPIC_API_KEY not found"

**Solution**:
1. Get API key from https://console.anthropic.com/
2. Add to `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

### Issue: "Image file not found"

**Solution**:
- Follow Step 3 to obtain receipt images
- Verify images are in `data/images/` directory
- Check filenames match test case `image_path` fields

### Issue: "Tool use not found in response"

**Possible Causes**:
1. Model may not support tool use (unlikely with Claude 3.5 Sonnet)
2. Prompt may be unclear
3. API rate limiting

**Solution**:
- Check Claude API status
- Verify you have API credits
- Review error messages in Langfuse traces

## Success Criteria

After completing all steps, you should have:

✅ Langfuse running and accessible at http://localhost:3000
✅ Dataset "receipt_inspection_v1" created with 10 items
✅ 10 receipt images in `data/images/`
✅ Single receipt processing works end-to-end
✅ Full evaluation suite completes successfully
✅ Traces visible in Langfuse UI with token usage and performance data
✅ Evaluation results saved to `eval_results/`
✅ Pass rate > 70% (target: 80-100%)

## Next Steps

Once testing is complete:

1. **Iterate on Prompts**: Use failed test cases to improve prompts
2. **Add More Test Cases**: Expand dataset with edge cases
3. **Experiment with Models**: Try different Claude models (Haiku, Opus)
4. **Monitor Production**: Deploy with Langfuse tracing enabled
5. **Track Metrics Over Time**: Use Langfuse to monitor degradation or improvement

## Questions?

- Check [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
- Review [README.md](../README.md) for general project information
- See OpenAI Cookbook: https://cookbook.openai.com/examples/partners/eval_driven_system_design/receipt_inspection
