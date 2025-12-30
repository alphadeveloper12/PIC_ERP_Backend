# RL Engine

This directory contains all scripts and models related to the Reinforcement Learning (RL) based ERC prediction and BOQ-to-Primavera linking system.

## Directory Structure

- `models/`: Contains the trained RL model weights, label encoders, and manual Primavera link mappings.
- `rl_feedback_loop.py`: Core logic for the RL agent and human feedback handling.
- `link_boq_primavera_rl.py`: Main script to link BOQ items to Primavera activities using the RL model and hierarchical context.
- `train_rl_model.py`: Script to train/fine-tune the RL model.
- `prepare_rl_dataset.py`: Prepares the dataset for RL training from raw BOQ/Primavera data.
- `apply_bulk_feedback.py`: Applies bulk ERC code corrections from a CSV file.
- `apply_primavera_feedback.py`: Applies bulk Primavera activity link corrections from a CSV file.
- `predict_boq_erc.py`: Standalone script to predict ERC codes for BOQ items.
- `data_processing.py`: Utility functions for cleaning BOQ and Primavera data.
- `data_augmentation_v2.py`: Script for augmenting training data to improve model robustness.
- `train_classifier.py`: Script to train the base classifier before RL fine-tuning.
- `predict.py`: Base prediction logic for the classifier.
- `test_primavera_feedback.py`: Verification script to test the feedback loop.

## Setup

To install the necessary dependencies (CPU-friendly):
```bash
cd rl_engine
pip install -r requirements.txt
```
*Note: If you want to ensure the CPU-only version of Torch is installed, you can run:*
`pip install torch --index-url https://download.pytorch.org/whl/cpu`

## Execution Examples

### 1. Linking BOQ to Primavera
To run the linking process with the latest RL model and hierarchical context:
```bash
cd rl_engine
python3 link_boq_primavera_rl.py
```
*Note: This script expects `boq.xlsx` and `primavera-p6.xlsx` in the `../inputs/` directory.*

### 2. Applying ERC Feedback
To correct ERC code predictions in bulk:
```bash
cd rl_engine
python3 apply_bulk_feedback.py path/to/erc_feedback.csv
```
*CSV Format: `Description,Correct_Shorthand`*

### 3. Applying Primavera Link Feedback
To correct Primavera activity links in bulk:
```bash
cd rl_engine
python3 apply_primavera_feedback.py path/to/primavera_feedback.csv
```
*CSV Format: `Title,Description,Correct_Activity_ID`*

### 4. Training the RL Model
To fine-tune the model on the prepared dataset:
```bash
cd rl_engine
python3 train_rl_model.py
```

## How it Works
1. **Context-Aware Linking**: The system combines the BOQ Title and Item Description to understand the full context of a work item.
2. **ERC Filtering**: It predicts an ERC code for the BOQ item and filters Primavera activities to only those matching the same broad category (e.g., 'CN' for Construction).
3. **Semantic Matching**: It uses SBERT embeddings to find the most similar Primavera activity within the filtered set.
4. **Human-in-the-Loop**: Manual corrections are stored in `models/` and prioritized in future runs, allowing the system to "learn" from your feedback.
