# TTS Bootcamp – code and commands (midterm)

Run everything from the kit root (the folder with `metrics.py`, `data/`, `baseline/`). This `code/`
folder sits next to the kit. `normalize.py` needs only the Python standard library.
`kaggle_run.ipynb` is the Kaggle notebook that ran the model steps on a free T4.

## AI assistant disclosure
I used Claude Code (Anthropic) as a coding assistant for environment setup, `code/normalize.py`, the
Kaggle notebook and helper scripts. `idea.md` is written by me. The normalizer rules
were developed against the validation items only; evaluation text was only passed through the finished
rules and checked mechanically (no digits, ₹ or % left, no new Latin letters).

## How the Task 1 tags were made
`metrics.py` reproduced the published numbers exactly (CER 0.2421, SIM 0.8303). All 14 items with
CER > 0.20 were tagged by comparing the expected `spoken` text with the Whisper transcript word by word
(repeated words, missing words, and which span carries the errors: numbers/dates/amounts versus
abbreviations versus English words). I could not listen to every clip, so only some were checked by ear.
`speaker_mismatch` was not used: all SIM values are 0.73 or higher.

## Deviation from the kit (please read)
`baseline/requirements.txt` pins IndicF5 at `fb652a96…`, which is the Hugging Face model revision, not a
GitHub commit, so `pip` fails ("not our ref"). I installed `f5_tts` from GitHub `main`
(`13f7c4d627cc10111aea8fe9c0039462cacacdc7`) with `--no-deps` (its `setup.py` wants `numpy<=1.26`,
the kit wants `numpy>=2.1`) and added its dependencies by hand; the model weights use the pinned revision
in `baseline/config.yaml`. Effect: 15 of the 16 non-hard validation items gave the same transcripts and CER
as the provided `baseline_val/`; `val_hi_05` moved from CER 0.000 to 0.020 with identical input text.

## Commands run
```bash
# Task 1 – score the provided baseline audio (Kaggle T4)
python metrics.py data/baseline_val --json out/baseline_val.json --csv out/baseline_val_scores.csv

# Task 2 – rule-based normalizer: normalized text for all 64 items (CPU, standard library only)
python code/normalize.py --items data/val_items.csv data/eval_items.csv \
    --out predictions/t2_normalized.csv

# Task 2 – synthesize the 40 evaluation items from the normalized text (Kaggle T4)
python baseline/run_baseline.py --items data/eval_items.csv --out predictions/t2_norm \
    --text-csv predictions/t2_normalized.csv --text-column normalized_text --seed 0

# Task 2 on validation (normalized text, everything else baseline); also the control for Task 3
python baseline/run_baseline.py --items data/val_items.csv --out predictions/val_control \
    --text-csv predictions/t2_normalized.csv --text-column normalized_text --seed 0
python metrics.py predictions/val_control --json out/val_control.json --csv out/val_control_scores.csv
```
Seed 0. Machine: Kaggle Tesla T4 (see `results.json`). Task 2 synthesis took 1161 s for the 40
evaluation items and 617 s for the 24 validation items.

## Results so far (validation, `metrics.py`)
| | CER | SIM | CER hard | CER hindi | CER hinglish | CER long |
|---|---|---|---|---|---|---|
| baseline | 0.2421 | 0.8303 | 0.4583 | 0.0342 | 0.3020 | 0.0318 |
| Task 2 text | 0.1231 | 0.8371 | 0.0989 | 0.0375 | 0.3020 | 0.0318 |
