# AI-tool usage disclosure

Update the bracketed fields before submitting. Do not claim activities that were not completed.

## Inside the product
- **Safety calculations:** no generative AI model is used at runtime. The prototype uses a physical WBGT calculation (Liljegren model through `thermofeel`), configured heat-stress thresholds, and a deterministic scheduler.
- **Supervisor messages:** fixed English/Tamil templates; no language model generates or changes safety instructions. Tamil wording still needs review by a fluent Tamil speaker and a safety professional.

## During development
- An AI assistant drafted portions of the code scaffold, tests, and documentation. The team must review, run, and understand the code before submission.
- **AI-assisted contribution:** [Describe honestly; do not guess a percentage.]
- **Work completed by the team:** [List only actions actually completed, such as running tests, reviewing assumptions, checking translations, or recording the demo.]
- **External validation:** [State whether real-data backtesting, supervisor interviews, and any sensor checks were actually completed. If not, say pending/not conducted.]

## Transparency
The bundled `data/sample_*_SYNTHETIC.csv` files are invented demonstration data, not observations. The real-data backtest requires a successful Open-Meteo download. Weather archive data is a reanalysis proxy, not worker-level or site-sensor measurements.
