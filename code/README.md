# TTS Bootcamp – code and commands

Run everything from the kit root (the folder with `metrics.py`, `data/`, `baseline/`). This `code/`
folder sits next to the kit. `normalize.py` (Task 2) and `en2dev.py` (Task 3) need only the Python standard
library. `kaggle_run.ipynb` (Tasks 1–2) and `kaggle_run_task3.ipynb` (Task 3) are the Kaggle notebooks that ran the
model steps on a free T4.

## AI assistant disclosure
I used Claude Code (Anthropic) as a coding assistant for environment setup, `code/normalize.py`,
`code/en2dev.py`, the Kaggle notebooks and helper scripts. `idea.md` and `report.md` are written by me. The normalizer rules
were developed against the validation items only; evaluation text was only passed through the finished
rules and checked mechanically (no digits, ₹ or % left, no new Latin letters). The same holds for
`en2dev.py`: its rules came from the 17 English words in the validation items plus general English
spelling patterns and a short list of irregular words; evaluation text was only passed through the finished
rules and counted (11 of 40 evaluation items contain English words; no Latin letters are left).

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

## Results (validation, `metrics.py`)
| | CER | SIM | CER hard | CER hindi | CER hinglish | CER long |
|---|---|---|---|---|---|---|
| baseline | 0.2421 | 0.8303 | 0.4583 | 0.0342 | 0.3020 | 0.0318 |
| Task 2 text (`val_control`) | 0.1231 | 0.8371 | 0.0989 | 0.0375 | 0.3020 | 0.0318 |
| Task 3 (`val_idea`) | 0.0582 | 0.8400 | 0.0989 | 0.0375 | 0.0421 | 0.0318 |

## Task 3: English words in Devanagari (`code/en2dev.py`)
```bash
# Task 3 text: Task 2 text, then every Latin-script word rewritten in Devanagari (CPU, standard library only)
python code/en2dev.py --in predictions/t2_normalized.csv --out predictions/t3_idea_text.csv

# validation (same 24 items, seed 0) and the 40 evaluation items (Kaggle T4)
python baseline/run_baseline.py --items data/val_items.csv --out predictions/val_idea     --text-csv predictions/t3_idea_text.csv --text-column idea_text --seed 0
python metrics.py predictions/val_idea --json out/val_idea.json --csv out/val_idea_scores.csv
python baseline/run_baseline.py --items data/eval_items.csv --out predictions/t3_idea     --text-csv predictions/t3_idea_text.csv --text-column idea_text --seed 0
```
Decoding settings are the baseline's (nfe_step 32, cfg 2.0), seed 0. Synthesis took 626 s (24 validation items)
and 1216 s (40 evaluation items) on the Kaggle T4.

How `en2dev.py` works: a word is looked up in a short list of irregular spellings; otherwise ordered
spelling rules (digraphs sh/ch/ph, silent letters, magic e, soft c/g, -tion, -ing, -er, -age, vowel pairs)
turn it into Hindi sounds, which are then written in Devanagari (matras, halant, anusvara). No model or
pronunciation dictionary is used.

Caveat: the validation gain on `hinglish` is in-sample, because the rules were tuned on the 17 English
words that appear in the validation items. As an out-of-sample check, 74 fresh English words written after
tuning were converted: 54 matched the usual Hindi spelling exactly and most others differed by one vowel.
An extra audio check on 12 new sentences with new English words (same seed, not part of the submission)
gave CER 0.353 with the Latin words and 0.023 with `en2dev.py`.

## Task 4: faster (`predictions/t4_fast/`)
Same text and system as Task 3, but fewer flow-matching steps (`--set nfe_step=N`). In ONE Kaggle T4 session the
notebook (`code/kaggle_run_task4.ipynb`) timed the baseline on the 24 validation items (baseline text,
nfe_step 32) and the Task 3 system at nfe_step 16, 12 and 8 (model loaded and one warm-up item excluded, as
`baseline/run_baseline.py` does), scored each with `metrics.py`, and **code** chose the fastest setting whose
validation CER stays within 1.2 x the Task 3 CER (0.0582, limit 0.0698):

| nfe_step | synthesis s (24 val items) | val CER | val SIM |
|---|---|---|---|
| 32 (baseline text) | 613.1 | (baseline) | |
| 16 | 327.9 | 0.0692 | 0.8433 |
| **12 (chosen)** | **246.2** | **0.0509** | 0.8411 |
| 8 | 165.2 | 0.0955 (fails the limit) | 0.8333 |

Speed-up = 613.092 / 246.164 = **2.49x**. Timing files: `code/baseline_timing.json` and `code/fast_timing.json`
(sweep summary: `code/t4_sweep.json`). The 40 evaluation clips in `predictions/t4_fast/` use nfe_step 12, seed 0.
Caveat: CER is not monotone in the step count here (12 steps scored lower than 16 and than 32), so differences of
this size are within run-to-run noise on 24 items; the 1.2x limit is checked on validation only.
