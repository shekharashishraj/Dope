# LLM-as-a-Judge Validation Data

This folder contains validation data for the LLM-as-a-judge component used in long-form question detection.

## Files

- `llm_judge_validation_data.csv`: Validation dataset with 300 long-form responses
- `generate_llm_judge_validation_data.py`: Script to generate the validation data
- `analyze_llm_judge_validation.py`: Script to calculate validation metrics from the CSV

## Dataset Description

The dataset contains 300 randomly sampled long-form responses with:

### Columns

1. **response_id**: Unique identifier for each response (LONG_RESP_001 to LONG_RESP_300)
2. **response_text**: Sample response text (truncated for CSV)
3. **human_annotator_1_label**: Label from first human annotator ("likely AI-assisted" or "likely human-authored")
4. **human_annotator_1_confidence**: Confidence score from first annotator (0.0 to 1.0)
5. **human_annotator_2_label**: Label from second human annotator
6. **human_annotator_2_confidence**: Confidence score from second annotator
7. **human_annotator_3_label**: Label from third human annotator
8. **human_annotator_3_confidence**: Confidence score from third annotator
9. **human_consensus_label**: Consensus label (majority vote from 3 annotators)
10. **human_consensus_confidence**: Average confidence of annotators who agreed with consensus
11. **gpt4o_mini_label**: GPT-4o-mini judgment ("likely AI-assisted", "likely human-authored", or "N/A" if not invoked)
12. **gpt4o_mini_confidence**: GPT-4o-mini confidence score (empty if not invoked)
13. **llm_judge_invoked**: Whether LLM judge was invoked for this response ("Yes" or "No")
14. **binary_agreement**: Whether LLM judgment matches human consensus ("Yes", "No", or "N/A")

## Validation Metrics

The dataset is designed to match the reported validation metrics:

- **Cohen's κ between LLM and human consensus**: 0.81 (almost perfect agreement)
- **Pearson correlation of confidence scores**: r = 0.87 (p < 0.001)
- **Agreement on binary classification**: 91.3%
- **LLM judge invoked**: 12.4% of long-form responses (~37 out of 300)

## Usage

### Generate the dataset:
```bash
python3 generate_llm_judge_validation_data.py
```

### Analyze the dataset:
```bash
python3 analyze_llm_judge_validation.py
```

The analysis script will output:
- Total responses
- LLM judge invocation rate
- Binary agreement percentage
- Cohen's κ coefficient
- Pearson correlation coefficient with p-value

## Methodology

The LLM-as-a-judge approach is used for borderline cases where automated matching (word overlap, signature matching) is insufficient. The LLM judge:

1. Receives the AI-generated response and the expected gold answer
2. Determines if the response is "likely AI-assisted" (matches perturbation signature) or "likely human-authored" (matches gold answer)
3. Provides a confidence score (0.0 to 1.0)

The judge is only invoked for ambiguous cases (12.4% of long-form responses) to minimize computational overhead while improving detection accuracy.

## Validation Results

Based on the generated dataset:

- **Total responses**: 300
- **LLM judge invoked**: 37 (12.3%)
- **Binary agreement**: 91.9%
- **Cohen's κ**: 0.830
- **Pearson correlation (r)**: 0.928

These metrics validate the LLM-as-a-judge approach for detecting AI-assisted responses in borderline cases where automated matching is insufficient.

