# Idea card

(1) Failure: english_word_error. Hinglish CER is 0.302 versus 0.034 for pure Hindi, so English words cause the errors. Items: val_hg_01, val_hg_06.

(2) Hypothesis and method: IndicF5 was probably trained mostly on Devanagari, so Latin-script words fall outside what it learned. Writing each English word in Devanagari, as an Indian speaker says it, should fix pronunciation. Method: hand-written rules mapping English spelling to Devanagari (sh, ch, th, silent final e, -tion, -ing), built from validation words plus a short exception list. One more english_word_error failure was identified, that was abbreviations. It was solved by the Task 2 normalizer which spells out abbreviations like RBI (hard CER 0.458 to 0.099).

(3) Prediction: hinglish CER falls from 0.302 to about 0.18 (roughly 40% relative); other categories unchanged, SIM within 0.03. Risk: irregular spellings such as "weekend" or "proper", where a wrong vowel is worse than Latin script.

(4) Result: hinglish CER fell from 0.302 to 0.042; other categories matched the Task 2 control. Caveat: the rules were made on validation words. On 12 unseen sentences, Latin text scored CER 0.353, converted text 0.023. Latin-script English words were the cause.
