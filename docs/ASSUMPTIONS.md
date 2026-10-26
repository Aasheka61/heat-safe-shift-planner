# Assumptions and sources

Verify every number below against the primary source before presenting it as fact.

| Item | Value used | Source / status |
|---|---|---|
| ISO 7243 WBGT limits, acclimatized (class 0/1/2/3) | 33 / 30 / 28 / 25 C | Secondary summaries of ISO 7243 (Czech ergonomics table; French ISO 7243:2017 calculator). **Check the standard.** Class 3 uses the conservative "no air movement" value (26 with air movement). |
| ISO 7243 limits, not acclimatized | 32 / 29 / 26 / 22 C | Same sources. |
| Metabolic class bounds | 65 / 130 / 200 / 260 W/m2 | Same sources. Class 4 is not supported (values differ between sources). |
| Resting metabolic rate in the work-rest formula | 65 W/m2 | Upper bound of class 0, as in the French calculator (a deliberately cautious choice). |
| Work fraction | f = (M_adm - 65)/(M_work - 65) | Same calculator (time-weighted metabolic rate). |
| Heavy / medium / light intensity | 230 / 190 / 110 W/m2 | ASSUMPTION. Chennai construction work was measured at 170-220 W/m2 (Venugopal et al., Global Health Action 2014, doi 10.3402/gha.v7.25283). Mapping real tasks to presets must be confirmed with supervisors and ISO 8996. |
| Clothing adjustment | 0 C default; +1 C woven coverall | French ISO 7243:2017 summary (+0 cotton, +1 woven coverall). Chennai construction clothing (saree/churidar with towels) is unmeasured; see Kuklane et al. 2014 for manikin tests. |
| Acclimatization | default: acclimatized | ASSUMPTION. New migrant workers may be unacclimatized; the app has a toggle. |
| WBGT model | Liljegren (thermofeel) | Liljegren et al. 2008. Simplified WBGT formula rejected: it overestimates in hot-humid regions (Lu & Romps 2022, Earth's Future). |
| Forecast buffer | calibrated 90th percentile of error | Estimated in the backtest (first half of days), applied to the second half. |
| Water break advice | every 20 minutes | Tamil Nadu regional meteorological centre advice (press report). |
| Latitude / longitude | 13.0827 N, 80.2707 E (Chennai) | Default pilot location. |
| Time zone | UTC+5:30 | India Standard Time. |
