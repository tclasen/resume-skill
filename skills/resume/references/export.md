# Export and verify a tailored resume

Finish the evidence review described in `references/assessment.md` and save a
validated assessment plan. Export locally with the same Python environment that
has `scripts/requirements.txt` installed:

```sh
python <skill-directory>/scripts/resume.py export --workspace <private-root> --file <private-root>/analyses/solo-engineer-v1.json --id solo-engineer-v1
```

The new private `outputs/solo-engineer-v1/` directory contains:

- `resume.pdf`: selectable text with embedded TrueType fonts and flowing pages.
- `resume.docx`: editable Word document with normal paragraphs and list items.
- `resume.md`: readable text version of the same selection.
- `evidence.md`: separate qualification findings, claim traces, sources, and
  verification/review states; links resolve to the private canonical bundles.
- `manifest.json`: output checksums, plan digest, paper size, and bundle hashes.

PDF and DOCX contain the selected personal text and section labels, without
internal evidence notes or source paths. The evidence report is private by
default; share it only when requested. Export never sends files or changes Git
remotes. Generated files are ignored by the data repository's output rules.

Use `--paper a4` for A4; the default is US Letter. The layout uses one column,
readable type, flowing paragraphs, and standard section headings. Long resumes
paginate rather than clipping. Prefer a concise selection appropriate to the
role; do not remove meaningful qualifications merely to fit one page.

The PDF uses ReportLab's bundled Bitstream Vera fonts. Unsupported characters
cause a clear failure before publication. Supply a TrueType font with suitable
coverage using `--font /absolute/path/font.ttf` and optionally
`--bold-font /absolute/path/bold.ttf`. When only a regular custom font is given,
it is used for both weights. Review shaping and reading order for scripts with
complex layout requirements. DOCX retains Unicode text and uses the viewer's
font substitution; pagination can differ between Word and other viewers.

The exporter revalidates the entire plan before and after rendering. It rejects
unconfirmed/disputed claims, stale evidence snapshots, missing derivation input
reviews, and unresolved local context links. A failed render cleans temporary
files. Existing output IDs are never replaced: use a new ID after edits.

## Final review

Open the rendered PDF and DOCX if a document viewer is available. Check name and
contact details, text extraction, accents, line wrapping, page breaks, and all
section content. Check that neither document exposes internal source notes.
Compare the resume against the evidence report: every factual line must retain
its meaning, scope, dates, attribution, and caveats. Numeric results must match
the reviewed derivation and measurement context.

If the host cannot open a document, state that limitation and verify selectable
PDF text and DOCX paragraph content with available tools. Never claim a visual
review that did not happen. Hand off both resume formats and the separate report
with clear private file paths. Commit canonical workspace changes only when the
user's repository instructions authorize or require it; never publish or send
documents without the user's authorization.
