# Demo video script (3-5 minutes, screen recording + voice)

1. **Problem (30 s).** "Construction workers in Tamil Nadu work fixed shifts in humid heat. Guidance is a blanket 12-3 pm advisory.
   Outdoor workers lose 24 days a year to heat [cite IIED]. Supervisors have no site-level trigger for when to stop."
2. **Idea (20 s).** "Every evening we tell the supervisor exactly when to work, slow down or stop, using a physical model and ISO 7243, not an AI guess."
3. **Live demo (90 s).** Run `streamlit run app.py`. Show: choose live forecast (or real data), pick tomorrow, show the WBGT chart against limits,
   the hour-by-hour schedule, the Tamil/English message, and download the stoppage log.
4. **Backtest (60 s).** Show the results table/chart from REAL data: safe vs overload minutes for 9-6, the 12-3 break, and the planner. State the
   numbers exactly and say the actual weather is an ERA5 proxy.
5. **Honest limits (30 s).** Forecast error and buffer, no sensor validation yet, ISO values to be verified, Tamil text under review.
6. **Impact and next steps (30 s).** Welfare board / builders as adopters, supervisor interviews, on-site sensor check, SMS/WhatsApp delivery.
7. **Close (10 s).** Team name, repo link.
