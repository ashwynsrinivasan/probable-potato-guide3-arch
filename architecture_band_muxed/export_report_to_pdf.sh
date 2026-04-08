#!/usr/bin/env bash
# Export TOSA_SPACING_YIELD_REPORT.md to PDF with figures.
# Run from the repository root (friendly-system-lmi) so image paths resolve:
#   cd /path/to/friendly-system-lmi && ./src/probable-potato-guide3-arch/architecture_band_muxed/export_report_to_pdf.sh
# Requires: pandoc, and a LaTeX engine (e.g. pdflatex) or --pdf-engine=wkhtmltopdf

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Script is in .../architecture_band_muxed/; repo root is 3 levels up (band_muxed -> probable-potato-guide3-arch -> src -> repo)
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
if [[ ! -f "$REPO_ROOT/src/probable-potato-guide3-arch/architecture_band_muxed/TOSA_SPACING_YIELD_REPORT.md" ]]; then
  echo "Run this script from the repository root, or ensure REPO_ROOT is correct."
  exit 1
fi

MD="$REPO_ROOT/src/probable-potato-guide3-arch/architecture_band_muxed/TOSA_SPACING_YIELD_REPORT.md"
OUT="${MD%.md}.pdf"
cd "$REPO_ROOT"
echo "Exporting $MD -> $OUT"
pandoc "$MD" -o "$OUT" -V geometry:margin=1in
echo "Done: $OUT"
