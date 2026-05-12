# Ecotron Platform Roadmap & TODOs

## Vision: The "Bloomberg-lite" for Indian Retail Traders
Transition Ecotron from a basic AI-powered trading platform to an all-in-one market intelligence terminal encompassing technical analysis, market structure, sentiment, macro events, options flow, risk management, and AI-assisted research.

---

## 1. Automated "Daily Ritual" Features (CRON Jobs)
*Goal: Create habit loops so traders check Ecotron every morning and evening.*
- [ ] **Implement APScheduler in `server.py`:** Add background task scheduling natively to the FastAPI backend.
- [ ] **Pre-Market AI Briefing (8:00 AM IST):** Automate `TradingAgentsGraph` runs for core indices (`^NSEI`, `^NSEBANK`) and top heavyweight stocks to generate morning setups, unusual volume alerts, and gap-up predictions.
- [ ] **Evening Recap (4:00 PM IST):** Automate end-of-day reports summarizing what moved markets, major institutional activity (FII/DII), and tomorrow's watchlist.

## 2. Programmatic SEO Flywheel
*Goal: Capture long-tail search traffic via dedicated, structured AI pages.*
- [ ] **Dynamic Landing Pages:** Automatically generate distinct URLs for high-intent searches based on the daily automated reports (e.g., `/nifty-support-resistance`, `/banknifty-open-interest-analysis`, `/best-swing-stocks-today`).
- [ ] **Structured Content & Schema:** Enhance frontend rendering to output FinancialProduct, FAQ, and Article structured data (JSON-LD) so AI search engines (ChatGPT, Perplexity) easily cite Ecotron.

## 3. Clear Positioning & Homepage UI Redesign
*Goal: Instantly communicate value over competitors like TradingView or Trendlyne.*
- [ ] **Refine Hero Messaging:** Update the homepage hero text to a sharper positioning statement: *"One dashboard for technical analysis, market news, FII/DII activity, options data, swing setups, and AI trade research for Indian traders."*
- [ ] **Speed & Performance:** Ensure the site feels instant (<2 sec load) with lightweight charts, Next.js/Vite SSR optimizations, and edge caching.

## 4. Viral Shareable Widgets
*Goal: Turn the platform's analysis into social currency for free acquisition.*
- [ ] Build downloadable/shareable widgets for Twitter, Telegram, and Reddit:
  - AI Probability of Breakout chart
  - Nifty Market Mood Meter
  - Sector Rotation Radar
  - Smart Money Flow mapping

## 5. Community Intelligence
*Goal: Increase retention by layering social proof and crowd sentiment.*
- [ ] Add bullish/bearish voting buttons on individual assets.
- [ ] Enable public strategy sharing and public watchlists.
- [ ] Build a top trader/analyst leaderboard based on prediction accuracy.

## 6. Trust Signals & Event-Driven Intelligence
*Goal: Establish absolute trust with the user base and capitalize on market events.*
- [ ] **Transparency UI:** Prominently display data sources, AI methodology, SEBI disclaimers, and historical hit rates.
- [ ] **Event-Driven Pages:** Create dedicated workflows and UI pages for massive traffic events (e.g., `/budget-2026-market-impact`, `/rbi-policy-live-analysis`).

## 7. Distribution Strategy
*Goal: Push content directly to where Indian traders live.*
- [ ] Set up automated Twitter/X bots to post daily charts, setups, and unusual flows.
- [ ] Create a Telegram channel for automated push alerts and heatmaps.
- [ ] Launch YouTube Shorts explaining AI-found breakouts and market levels.
