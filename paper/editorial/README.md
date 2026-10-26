# Editable earlier-study sections

The combined manuscript builder in `../combined_study/build_manuscript.py` reads the earlier sections here directly. Edit `replication.tex` for the expanded warning cohort and cancellation fixtures; edit the other section files for their named studies. These remain LaTeX fragments, with packages, labels and bibliography supplied by a parent manuscript.

`manuscript.tex` in this directory retains the historical assembly. `substantive_evaluation/make_draft.py` builds that historical entry point, not the current combined paper. Statistical generators continue to write original reports under `../generated/`. Reconcile any numerical changes with the frozen evidence before editing reported quantities. The combined builder records the exact section and generated-table hashes it consumes.
