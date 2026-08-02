ANET | Investment Identification Report 

# **ARISTA NETWORKS** 

## **Investment Identification Report** 

**NYSE: ANET  |  STAGED ACCUMULATE** 

Page 1 

ANET | Investment Identification Report 

### **Table of Contents** 

|Executive Investment Decision ..................................................................................................................................... 3|
|---|
|1 Investment Mandate and Company Lens ................................................................................................................... 3|
|2 Business Quality and Growth Engine ........................................................................................................................ 4|
|3 Five-Lens Fundamental Dashboard ........................................................................................................................... 4|
|3.1 Profitability ......................................................................................................................................................... 4|
|3.2 Growth ................................................................................................................................................................ 5|
|3.3 Capital Structure and Solvency ........................................................................................................................... 6|
|3.4 Liquidity and Cash-Flow Quality ....................................................................................................................... 7|
|3.5 Valuation ............................................................................................................................................................. 8|
|4 Market Behaviour, CAPM and Forward Signal ......................................................................................................... 9|
|4.1 Moving Averages, Bollinger Bands and RSI ...................................................................................................... 9|
|4.2 Five-Year Daily CAPM Regression ................................................................................................................. 11|
|5 Benchmark, Catalysts and Risk Ledger ................................................................................................................... 11|
|6 Portfolio Recommendation and Monitoring Rules .................................................................................................. 13|
|References ................................................................................................................................................................... 14|
|Appendix A - Complete Jupyter Notebook Code ....................................................................................................... 16|



Page 2 

ANET | Investment Identification Report 

### **Executive Investment Decision** 

Arista Networks (ANET) has a STAGED ACCUMULATE rating for a diversified growth investor with a 5-year investment time horizon and a stomach for volatility. The company is unusually strong operationally as revenue compounded to 27.1%, net income at 37.4% and free cash flow in FY2025 was US$4.25bn. Q1 2026 revenue then rose 35.1% year on year to US$2.709bn while GAAP operating margin held at 42.7% (Arista, 2026b). The catch is at US$168.61, which is 37.7× forward earnings and 20.6× EV/revenue. With a probability-weighted sensitivity of US$191.39 (+13.5%) comes a CAPM beta of 1.60 and a historical maximum drawdown of -50.4%. Start with a 2% weight and build up or pick and choose and limit the weight to 4% of the portfolio. 

|**Decision metric**|**Evidence**|
|---|---|
|Recommendation|STAGED ACCUMULATE|
|Price / expected value|US$168.61 / US$191.39|
|Forward P/E / EV-revenue|37.7× / 20.6×|
|Revenue / net-income CAGR|27.1% / 37.4%|
|CAPM beta / R²|1.60 / 32.2%|
|Client fit|Diversified, high-volatility growth mandate|



### **1 Investment Mandate and Company Lens** 

The questions in this report are whether a firm can increase its intrinsic value from a structural growth opportunity without taking on an inappropriate portfolio risk. ANET was selected in preference to NVIDIA or Broadcom because it offers a unique way to get exposure to AI networking via switching, routing and software. Evidence is a mix of Yahoo Finance annual accounts and daily prices, FY2025 Audited 10-K and Q1 2026 results and sector research. The various components of growth can be analyzed in terms of ratio decomposition of growth, which provides an analysis of growth with reference to margin and asset use (Lev and Thiagarajan, 1993; Fairfield and Yohn, 2001; Nissim and Penman, 2001). Because accrual earnings can lead to a misstatement of persistence (Sloan, 1996; Dechow, Ge and Schrand, 2010), cash conversion is tested, and solvency, peer multiples, technical indicators and CAPM link the quality of a company to a potential return a client might receive. All calculations, figures and the regression are shown in the worked notebook. Intrinsic value is done by triangulation as opposed to a “one-point DCF” forecast. Historical ratios provide a measure of earnings quality; peer multiples provide an indication of the expectations that are already priced; CAPM provides a framework for systematic risk; and scenario analysis allows one to analyze how forward EPS growth and exit multiples work together. Daily series have been adjusted to remove the effect of the stock split in December 2024. They are returned continuously aligned by common trading dates, the annual Treasury yield is divided by 252 and Newey-West standard errors account for short-run dependence. This design renders assumptions apparent and avoids a positive chart becoming the recommendation in and of itself. 

Page 3 

ANET | Investment Identification Report 

### **2 Business Quality and Growth Engine** 

Arista manufactures high-speed Ethernet switches, routers and provides subscription software solutions for AI center, cloud/data center, campus and wide-area networks. It features a single software image when operating on platforms; Cloud-Vision provides automation, telemetry and policy control. This installed software architecture leads to switching costs and offers product extension beyond hyperscale switching (Arista, 2026a). The demand is the material one: IDC estimates that data-center Ethernet sales rose to a total of US$10.0bn in Q1 2026, increasing 61.0% year on year. Arista earned US$2.2bn in Ethernet-switch revenues, up 37.3%, accounting for 20.7% of datacenter Ethernet-switch revenues (IDC, 2026). The moat is thus not “AI” as a label, but the group of EOS consistency, qualification of customers, execution at high speed 400G/800G, and its growing campus/AI-spine products. The company's Q2 2026 guidance was US$2.8bn revenue and non-GAAP operating margin of 46-47% (Arista, 2026b). For the customers, the combination of the product with the software also has an economic benefit: heterogeneous estates can be automated using the same one operating architecture, without having to maintain any code base for each individual device, allowing for innovation. But customer concentration, capital expenditures cycles in the cloud, component supply, export controls and rapid product substitution are material. Although the data-center Ethernet category is appealing and competitive, NVIDIA's success in Q1 2026 saw it become the top provider. There is a need for share resilience, not just market growth, in the report. 

### **3 Five-Lens Fundamental Dashboard** 

#### **3.1 Profitability** 

The larger the business the more profitable it was. FY2025 revenue was US$9.01bn, net income US$3.51bn, gross margin 64.1%, operating margin 42.8% and net margin 39.0%. The chart illustrates that while gross margin continued to stabilize around 64%, operating margin continued to grow, which was the result of operating leverage, rather than revenue acquired on the back of weaker economics. ROE alone is not informative as the mechanical effect of capital structure on equity returns can be observed (Modigliani and Miller, 1958). The interest income and debt free balance sheet are also reflected in the operating margin as compared to net margin. The outcome is that it can be used to support higher intrinsic value, without the need for price and/or warranty and/or development-cost concessions due to competition. The whole contraction of the operating margin, which is 2 points, would be more telling than a revenue misses in a single quarter as it could be an indication of a fading differentiation. 

Page 4 

ANET | Investment Identification Report 



**_Figure 1. Profitability architecture: revenue and earnings scale with margins. Source: Yahoo Finance annual statements. Currency: USD. Units: US$ billions and percent. Period: FY2022–FY2025._** 

#### **3.2 Growth** 

Revenue rose from US$4.38bn in FY2022 to US$9.01bn in FY2025, a 27.1% CAGR. Net income grew at 37.4% , with the FY2022 net income number being unusually low (as a percent of revenue), thus making the free-cash-flow CAGR rate look higher at 111.7%. The continued sales growth and increasing conversion are the two key signals. Growth is only valuable if it is accompanied by above-average returns on investment, and residual-income logic does not value growth per se, but instead above-average returns on investment (Ohlson, 1995). The growth during Q1 2026 is a good indicator of heading in the right direction but can't be sustained forever. A sustainable case requires that AI networking becomes more than just a few hyperscale deployments and starts to be used for repeat spine, switching, optics and campus use; if it doesn't, customer timing may make the annual growth rate much more volatile than the suggested CAGR. 

Page 5 

ANET | Investment Identification Report 



**_Figure 2. Growth velocity and three-year CAGR bridge. Source: Yahoo Finance annual statements; author calculations. Currency: USD. Units: US$ billions and CAGR percent. Period: FY2022–FY2025._** 

#### **3.3 Capital Structure and Solvency** 

FY2025 cash and short-term investments totaled US$10.74bn, while reported debt was essentially zero resulting in the same net-cash buffer of US$10.74bn. The equity share contributed the majority of assets and there was no debt/equity ratio. This eliminates refinancing risk, interest-rate risk and offers breathing room for re-stock, research, re-purchasing or acquisition. Where innovation cycles are not always predictable, having financial flexibility is useful, but over-liquidity can cause efficiency of assets to decline. The conservative stance is in keeping with pecking order theory which states that profitable companies can fund investments internally and forego the higher cost of external funds (Myers, 1984). Solvency is certainly an advantage, and not the source of the valuation risk. 

Page 6 

ANET | Investment Identification Report 



**_Figure 3. Capital structure and solvency buffer. Source: Yahoo Finance annual balance sheets; author calculations. Currency: USD. Units: US$ billions and debt/equity percent. Period: FY2022–FY2025._** 

#### **3.4 Liquidity and Cash-Flow Quality** 

The current and quick ratio of FY2025 were 3.05× and 2.63×, respectively, which is a comfortably higher than 1.0×. This meant an operating cash flow equal to 1.25× net income and a free cash flow of 1.21× compared to a poor cash flow conversion in FY2022. This is important as cash backed earnings have a stronger persistence than accrual backed growth (Sloan, 1996; Piotroski, 2000). However, inventory still ballooned to approximately US$2.25bn in FY2025, which could result in write-down risk or working-capital risk if there is a pause in demand. Keep an eye on the days in inventory and days in receivables and not just the current ratio, as a high current ratio does not necessarily result in a profit. 

Page 7 

ANET | Investment Identification Report 



**_Figure 4. Liquidity headroom and cash conversion. Source: Yahoo Finance annual statements; author calculations. Currency: USD. Units: ratios (×) and US$ billions. Period: FY2022–FY2025._** 

|**FY**|**Revenue (US$bn)**|**Operating margin**|**Current ratio**|**CFO / NI**|
|---|---|---|---|---|
|2022|4.38|34.9%|4.29×|0.36×|
|2023|5.86|38.5%|4.38×|0.97×|
|2024|7.00|42.0%|4.36×|1.30×|
|2025|9.01|42.8%|3.05×|1.25×|



#### **3.5 Valuation** 

With forward earnings multiple of 37.7, ANET trades at about 23.4× for Cisco, and 23.1× for F5. The premium is due to a higher growth and margin in the recent past, but EV/revenue of 20.6× is not forgiving. The peer scatter is descriptive, as it incorporates HPE's acquired Juniper business. Multiples are simply statements of expectations; they don't by themselves determine value. Thus, scenario analysis involves both changing the levels of EPS growth and the level of the terminal multiple, which should reflect the sensitivity required in practice when distant forecasts are more important than value (Graham and Harvey, 2001). US$191.39 is near the US$191.75 mean estimate among analysts whereas the bear case is US$150.11. The 25/50/25 probabilities are carefully weighted, and if there is a 10-percentage-point increase in bull, then there will be a 10-percentage-point decrease in bear, with a corresponding material change in expected value. Therefore, the size of the position is a valuation control: Multiplecompression risk is not eliminated with business quality. 

Page 8 

ANET | Investment Identification Report 



**_Figure 5. Peer valuation-growth map. Source: Yahoo Finance company snapshots. Currency: USD. Units: multiples (×), percent and US$bn bubble size. Period: snapshot 17 Jul 2026; forward/trailing fields._** 

|**Scenario**|**Probability**|**EPS growth**|**Terminal P/E**|**Implied price**|**Return**|
|---|---|---|---|---|---|
|Bear|25%|12%|30.0×|US$150.11|-11.0%|
|Base|50%|20%|35.0×|US$187.63|+11.3%|
|Bull|25%|28%|42.0×|US$240.17|+42.4%|



### **4 Market Behaviour, CAPM and Forward Signal** 

#### **4.1 Moving Averages, Bollinger Bands and RSI** 

At 17 July 2026, adjusted price was US$168.61, above the 50-day SMA (US$160.66) and 200-day SMA (US$144.73), so the long trend remains positive. Price was not overbought on the RSI(14) which was at 49.5, and price was in between the Bollinger bands of US$153.71 and US$187.99. But MACD (3.62) was in bear market territory relative to its signal (4.35), which generated a choppy near-term chart. Evidence of moving-average rules and annualized e price patterns can be found (Brock, Lakonishok and LeBaron, 1992; Lo, Mamaysky and Wang, 2000), and momentum evidence is found across horizons and markets (Jegadeesh and Titman, 1993; Asness, Moskowitz and Pedersen, 2013). However sentiment can outweigh fundamentals (Barberis, Shleifer and Vishny 1998), indicators should be used to time tranches, not to replace valuation. 

Page 9 

ANET | Investment Identification Report 



**_Figure 6. Price trend architecture and trading volume. Source: Yahoo Finance adjusted daily prices. Currency: USD. Units: US$/share and million shares. Period: three years ending 17 Jul 2026._** 



**_Figure 7. Bollinger volatility envelope and RSI momentum regime. Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: US$/share, standard deviations and RSI index (0–100). Period: one year ending 17 Jul 2026._** 

Page 10 

ANET | Investment Identification Report 

#### **4.2 Five-Year Daily CAPM Regression** 

Daily CAPM is based on 1,265 common observations in the daily period 02 July 2021–17 July 2026. Against the S&P 500 and a daily 13-week T-bill proxy, beta is 1.60 (p<0.001), R² 32.2%, and annualized alpha 40.2% (HAC p=0.040). ANET historically had a 1% market move for a 1.6% move, and positive abnormal return, though the low explanatory power suggests that a lot of the variation is driven by firm specific shocks. CAPM provides, however, a disciplined risk/return benchmark (Sharpe, 1964; Lintner, 1965) and is known to have some limitations, in particular size and value effects and parameter instability (Fama and French, 1992, 2004). Alpha is not a prediction, it's historical information. 

|**CAPM output**|**Python regression result**|
|---|---|
|Daily observations|1,265|
|Beta (market excess return)|1.601|
|Annualised alpha|40.2%|
|Alpha HAC p-value|0.040|
|R-squared|32.2%|
|Latest T-bill proxy|3.707%|





<!-- Start of picture text -->
Latest T-bill proxy 3.707%<br><!-- End of picture text -->

**_Figure 8. CAPM security characteristic line with Newey–West inference. Source: Yahoo Finance adjusted daily prices and 13-week T-bill yield; author OLS-HAC regression. Currency: USD. Units: daily excess-return percent. Period: 02 Jul 2021–17 Jul 2026._** 

### **5 Benchmark, Catalysts and Risk Ledger** 

During the common analysis period (2 July 2021 to 17 July 2026), ANET's CAGR is 48.8%, while the Sharpe ratio is 1.00, significantly outpacing the CAGR of its peer, S&P 500 of 11.4% with a Sharpe ratio of 0.52, and XLK of 

Page 11 

ANET | Investment Identification Report 

19.6% CAGR and 0.69 Sharpe ratio. But this outperformance came with a lot of risk: ANET's annualized volatility was 47.8% versus the S&P 500's 17.0% and the XLK's 25.5%. Its maximum drawdown was −50.4%, versus −25.4% for the S&P 500 and −33.6% for XLK. While ANET's historical return may be read as a risk-free example, the two breaks are partially attributable to the attributes of its beta, company specific and its concentrated growth. XLK is deemed to be the most relevant operating benchmark because it mimics the technology sector and the S&P 500 mimics the client's broad market opportunity cost. The monthly heatmap also shows that ANET returns have been long-term in a compounding manner but have been sporadic with significant intramonthly losses. Some possible catalysts are a continued strong trend in 800G adoption, further gains in next generation Ethernet, ongoing successes in EOS and Cloud-Vision growth, growth in the campus market and continued margin discipline. Key risks include competition with NVIDIA and Cisco, reliance on large cloud customers, hyper-scaler capital spending cuts, inventory and supply-chain distortions, export control limitations and geopolitical risks and premium deration. Thus, ANET would suit a diversified growth mandate with substantial exposure to volatility and would not be appropriate for an income-oriented mandate or capital preservation mandate. 

|**Asset**|**CAGR**|**Volatility**|**Sharpe**|**Max drawdown**|
|---|---|---|---|---|
|ANET|48.8%|47.8%|1.00|-50.4%|
|S&P 500|11.4%|17.0%|0.52|-25.4%|
|XLK|19.6%|25.5%|0.69|-33.6%|





**_Figure 9. Benchmark-relative wealth and drawdown. Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: growth of US$100 (log scale) and drawdown percent. Period: 02 Jul 2021–17 Jul 2026._** 

Page 12 

ANET | Investment Identification Report 



**_Figure 10. ANET monthly return heatmap. Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: monthly total-return percent. Period: Jul 2021–Jul 2026._** 

### **6 Portfolio Recommendation and Monitoring Rules** 

Recommendation: Do not randomly buy in the market but STAGED ACCUMULATE. Add 2% at the current US$168.61; add 1% if evidence of operating below US$155.12 and add 1% only after revenue/margin confirmation. The probability-weighted 12-month value is US$191.39 with a valuation range of US$187.63 to US$240.17, reflecting that valuation is more of an art than a science. Avoid Averaging Down if quarterly revenue growth is less than 20%, GAAP operating margin is less than 38%, net-cash balance is down more than 25% without a value creating explanation, and the competitive share thesis is broken. Risk review is done if there is a simultaneous close below the 200-day SMA and RSI is below 45, NOT automatic sale. This rule set maintains exposure to an outstanding growth/quality franchise, while staying within a 1.60 beta, 37.7× forward multiple and 50% drawdown capacity. The recommendation is based on suitability and diversification and evidence (not past return). 

|**Rule**|**Action**|
|---|---|
|Initial exposure|2% near US$168.61|
|Second tranche|Add 1% at/below US$155.12 if thesis is intact|
|Maximum exposure|4% after results confirm growth and margins|
|Fundamental review|Revenue growth <20%; GAAP operating margin <38%; net cash -25%|
|Technical review|Close below 200-day SMA with RSI below 45|
|Suitable client|Diversified growth investor; not income/capital-preservation mandate|



Page 13 

ANET | Investment Identification Report 

### **References** 

Asness, C.S., Moskowitz, T.J. and Pedersen, L.H. (2013) ‘Value and momentum everywhere’, Journal of Finance, 68(3), pp. 929–985. <u>Link</u> 

Barberis, N., Shleifer, A. and Vishny, R. (1998) ‘A model of investor sentiment’, Journal of Financial Economics, 49(3), pp. 307–343. <u>Link</u> 

Brock, W., Lakonishok, J. and LeBaron, B. (1992) ‘Simple technical trading rules and the stochastic properties of stock returns’, Journal of Finance, 47(5), pp. 1731–1764. <u>Link</u> 

Dechow, P., Ge, W. and Schrand, C. (2010) ‘Understanding earnings quality’, Journal of Accounting and Economics, 50(2–3), pp. 344–401. <u>Link</u> 

Fairfield, P.M. and Yohn, T.L. (2001) ‘Using asset turnover and profit margin to forecast changes in profitability’, Accounting Review, 76(4), pp. 371–385. <u>Link</u> 

Fama, E.F. and French, K.R. (1992) ‘The cross-section of expected stock returns’, Journal of Finance, 47(2), pp. 427–465. <u>Link</u> 

Fama, E.F. and French, K.R. (2004) ‘The capital asset pricing model: theory and evidence’, Journal of Economic Perspectives, 18(3), pp. 25–46. Link 

Graham, J.R. and Harvey, C.R. (2001) ‘The theory and practice of corporate finance’, Journal of Financial Economics, 60(2–3), pp. 187–243. <u>Link</u> 

Jegadeesh, N. and Titman, S. (1993) ‘Returns to buying winners and selling losers’, Journal of Finance, 48(1), pp. 65–91. <u>Link</u> 

Lev, B. and Thiagarajan, S.R. (1993) ‘Fundamental information analysis’, Journal of Accounting Research, 31(2), pp. 190–215. <u>Link</u> 

Lintner, J. (1965) ‘The valuation of risk assets and the selection of risky investments’, Review of Economics and Statistics, 47(1), pp. 13–37. <u>Link</u> 

Lo, A.W., Mamaysky, H. and Wang, J. (2000) ‘Foundations of technical analysis’, Journal of Finance, 55(4), pp. 1705–1765. <u>Link</u> 

Modigliani, F. and Miller, M.H. (1958) ‘The cost of capital, corporation finance and the theory of investment’, American Economic Review, 48(3), pp. 261–297. <u>Link</u> 

Myers, S.C. (1984) ‘The capital structure puzzle’, Journal of Finance, 39(3), pp. 575–592. <u>Link</u> 

Nissim, D. and Penman, S.H. (2001) ‘Ratio analysis and equity valuation’, Review of Accounting Studies, 6, pp. 109–154. <u>Link</u> 

Ohlson, J.A. (1995) ‘Earnings, book values, and dividends in equity valuation’, Contemporary Accounting Research, 11(2), pp. 661–687. Link 

Piotroski, J.D. (2000) ‘Value investing: the use of historical financial statement information’, Journal of Accounting Research, 38, pp. 1–41. <u>Link</u> 

Page 14 

ANET | Investment Identification Report 

Sharpe, W.F. (1964) ‘Capital asset prices: a theory of market equilibrium under conditions of risk’, Journal of Finance, 19(3), pp. 425–442. <u>Link</u> 

Sloan, R.G. (1996) ‘Do stock prices fully reflect information in accruals and cash flows about future earnings?’, Accounting Review, 71(3), pp. 289–315. <u>Link</u> 

Bollinger, J. (2002) Bollinger on Bollinger Bands. New York: McGraw-Hill. Link 

Wilder, J.W. (1978) New Concepts in Technical Trading Systems. Greensboro, NC: Trend Research. <u>Link</u> 

Arista Networks, Inc. (2026a) Annual Report on Form 10-K for the year ended 31 December 2025. Available at: SEC EDGAR (Accessed: 20 July 2026). <u>Link</u> 

Arista Networks, Inc. (2026b) ‘First quarter 2026 financial results’, 5 May. Available at: Arista Investor Relations (Accessed: 20 July 2026). <u>Link</u> 

IDC (2026) ‘NVIDIA becomes #1 in datacenter Ethernet switching as 1Q26 market surges 39.8%’, June. Available at: IDC (Accessed: 20 July 2026). Link 

Yahoo Finance (2026) ANET, ^GSPC, XLK and ^IRX historical prices, financial statements and company statistics. Available at: Yahoo Finance (Accessed: 20 July 2026). <u>Link</u> 

Page 15 

ANET | Investment Identification Report 

### **Appendix A  Complete Jupyter Notebook Code** 

**Code cell 1** 

```
from pathlib import Path
import json
import os
import warnings
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import yfinance as yf
from IPython.display import display, Markdown
warnings.filterwarnings("ignore", category=FutureWarning)
ROOT = Path.cwd()
CACHE = ROOT / ".yf_cache"
CACHE.mkdir(exist_ok=True)
yf.set_tz_cache_location(str(CACHE))
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 220,
    "font.family": "DejaVu Sans",
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelsize": 10,
})
NAVY = "#0B1F3A"
TEAL = "#0B8F87"
CYAN = "#4CC9F0"
GOLD = "#F4B942"
RED = "#D1495B"
SLATE = "#62748A"
GREEN = "#2E8B57"
def finish_figure(fig, filename, footer):
    # Add the required evidence footer, save, display and close a figure.
    fig.text(0.01, 0.012, footer, fontsize=7.4, color="#46515F")
    fig.tight_layout(rect=(0, 0.045, 1, 0.98))
    fig.savefig(ROOT / filename, bbox_inches="tight", facecolor="white")
    plt.show()
    plt.close(fig)
print("Analysis environment ready:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
```

**Code cell 2** 

```
TICKER = "ANET"
MARKET = "^GSPC"
```

Page 16 

ANET | Investment Identification Report 

```
SECTOR = "XLK"
```

```
RISK_FREE = "^IRX"
START_DATE = "2021-07-01"
END_DATE = (pd.Timestamp.today().normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
```

```
def download_ohlcv(symbol):
    frame = yf.download(
        symbol,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if frame.empty:
        raise RuntimeError(f"Yahoo Finance returned no data for {symbol}")
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "Date"
    return frame.sort_index()
```

```
anet_px = download_ohlcv(TICKER)
market_px = download_ohlcv(MARKET)
sector_px = download_ohlcv(SECTOR)
rf_px = download_ohlcv(RISK_FREE)
```

```
anet_px.to_csv(ROOT / "anet_price_data.csv")
market_px.to_csv(ROOT / "sp500_price_data.csv")
sector_px.to_csv(ROOT / "xlk_price_data.csv")
rf_px.to_csv(ROOT / "risk_free_price_data.csv")
```

```
price_audit = pd.DataFrame({
```

- `"Series": [TICKER, MARKET, SECTOR, RISK_FREE],` 

```
    "First observation": [anet_px.index.min(), market_px.index.min(), sector_px.index.min(), rf_px.index.min()],
    "Last observation": [anet_px.index.max(), market_px.index.max(), sector_px.index.max(), rf_px.index.max()],
    "Rows": [len(anet_px), len(market_px), len(sector_px), len(rf_px)],
```

```
})
display(price_audit)
display(anet_px.tail())
```

##### **Code cell 3** 

```
company = yf.Ticker(TICKER)
income = company.income_stmt.copy()
balance = company.balance_sheet.copy()
cashflow = company.cashflow.copy()
info = company.info
```

```
def row(frame, labels, default=np.nan):
```

```
    if isinstance(labels, str):
        labels = [labels]
    for label in labels:
        if label in frame.index:
            return pd.to_numeric(frame.loc[label], errors="coerce")
    return pd.Series(default, index=frame.columns, dtype=float)
```

```
years = sorted(set(income.columns) & set(balance.columns) & set(cashflow.columns))[-4:]
```

Page 17 

ANET | Investment Identification Report 

```
years = pd.DatetimeIndex(years)
fund = pd.DataFrame(index=years)
fund.index.name = "Fiscal Year"
```

```
fund["Revenue"] = row(income, "Total Revenue").reindex(years)
fund["Gross Profit"] = row(income, "Gross Profit").reindex(years)
fund["Operating Income"] = row(income, "Operating Income").reindex(years)
fund["Net Income"] = row(income, "Net Income").reindex(years)
fund["Total Assets"] = row(balance, "Total Assets").reindex(years)
fund["Current Assets"] = row(balance, "Current Assets").reindex(years)
fund["Current Liabilities"] = row(balance, "Current Liabilities").reindex(years)
fund["Cash & Short Investments"] = row(
    balance,
```

```
    ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"],
).reindex(years)
fund["Inventory"] = row(balance, "Inventory", 0).reindex(years).fillna(0)
fund["Total Debt"] = row(balance, "Total Debt", 0).reindex(years).fillna(0)
fund["Equity"] = row(balance, ["Stockholders Equity", "Total Equity Gross Minority Interest"]).reindex(years)
fund["Operating Cash Flow"] = row(cashflow, "Operating Cash Flow").reindex(years)
fund["Capital Expenditure"] = row(cashflow, "Capital Expenditure").reindex(years)
fund["Free Cash Flow"] = row(cashflow, "Free Cash Flow").reindex(years)
```

```
fund["Gross Margin"] = fund["Gross Profit"] / fund["Revenue"]
fund["Operating Margin"] = fund["Operating Income"] / fund["Revenue"]
fund["Net Margin"] = fund["Net Income"] / fund["Revenue"]
fund["ROA"] = fund["Net Income"] / fund["Total Assets"]
fund["Revenue Growth"] = fund["Revenue"].pct_change()
fund["Net Income Growth"] = fund["Net Income"].pct_change()
fund["FCF Growth"] = fund["Free Cash Flow"].pct_change()
fund["Debt / Equity"] = fund["Total Debt"] / fund["Equity"]
fund["Equity / Assets"] = fund["Equity"] / fund["Total Assets"]
fund["Net Cash"] = fund["Cash & Short Investments"] - fund["Total Debt"]
fund["Current Ratio"] = fund["Current Assets"] / fund["Current Liabilities"]
fund["Quick Ratio"] = (fund["Current Assets"] - fund["Inventory"]) / fund["Current Liabilities"]
fund["CFO / Net Income"] = fund["Operating Cash Flow"] / fund["Net Income"]
fund["FCF / Net Income"] = fund["Free Cash Flow"] / fund["Net Income"]
fund["FCF Margin"] = fund["Free Cash Flow"] / fund["Revenue"]
```

```
fund.to_csv(ROOT / "anet_fundamentals_and_ratios.csv")
ratio_view = fund[[
    "Revenue", "Net Income", "Free Cash Flow", "Gross Margin", "Operating Margin",
    "Net Margin", "Revenue Growth", "Net Cash", "Debt / Equity", "Current Ratio",
    "Quick Ratio", "CFO / Net Income", "FCF / Net Income",
```

```
]].copy()
```

```
ratio_view[["Revenue", "Net Income", "Free Cash Flow", "Net Cash"]] /= 1e9
ratio_view = ratio_view.rename(columns={
    "Revenue": "Revenue (US$bn)", "Net Income": "Net income (US$bn)",
    "Free Cash Flow": "FCF (US$bn)", "Net Cash": "Net cash (US$bn)"
```

```
})
display(ratio_view.round(3))
```

##### **Code cell 4** 

```
# Figure 1 - Profitability architecture
```

```
fy = fund.index.year.astype(str)
fig, ax = plt.subplots(figsize=(11.2, 6.2))
x = np.arange(len(fy))
```

```
w = 0.19
```

Page 18 

ANET | Investment Identification Report 

```
for offset, col, color, label in [
    (-1.5*w, "Revenue", NAVY, "Revenue"),
    (-0.5*w, "Gross Profit", TEAL, "Gross profit"),
    (0.5*w, "Operating Income", GOLD, "Operating income"),
    (1.5*w, "Net Income", RED, "Net income"),
]:
    bars = ax.bar(x + offset, fund[col] / 1e9, w, color=color, label=label)
    ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=7)
ax.set_xticks(x, fy)
ax.set_ylabel("US$ billions")
ax.set_title("Profitability architecture: scale and earnings expanded together")
ax.legend(ncol=4, frameon=False, loc="upper left")
ax2 = ax.twinx()
for col, color, marker in [
    ("Gross Margin", TEAL, "o"), ("Operating Margin", GOLD, "s"), ("Net Margin", RED, "D")
]:
    ax2.plot(x, fund[col] * 100, color=color, marker=marker, linewidth=2.0, linestyle="--")
ax2.set_ylabel("Margin (%)")
ax2.set_ylim(0, max(75, fund["Gross Margin"].max() * 115))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
finish_figure(
    fig, "figure_01_profitability.png",
    "Source: Yahoo Finance annual statements. Currency: USD. Units: US$ billions and percent. Period: FY2022–
FY2025."
)
```

##### **Code cell 5** 

```
# Figure 2 - Growth velocity: value and CAGR bridge
periods = len(fund) - 1
cagrs = {
    "Revenue": (fund["Revenue"].iloc[-1] / fund["Revenue"].iloc[0]) ** (1 / periods) - 1,
    "Net income": (fund["Net Income"].iloc[-1] / fund["Net Income"].iloc[0]) ** (1 / periods) - 1,
    "Free cash flow": (fund["Free Cash Flow"].iloc[-1] / fund["Free Cash Flow"].iloc[0]) ** (1 / periods) - 1,
}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.5), gridspec_kw={"width_ratios": [1.35, 1]})
ax1.plot(fy, fund["Revenue"] / 1e9, color=NAVY, marker="o", linewidth=3, label="Revenue")
ax1.plot(fy, fund["Net Income"] / 1e9, color=RED, marker="D", linewidth=2.5, label="Net income")
ax1.plot(fy, fund["Free Cash Flow"] / 1e9, color=TEAL, marker="s", linewidth=2.5, label="Free cash flow")
ax1.set_ylabel("US$ billions")
ax1.set_title("Absolute growth path")
ax1.legend(frameon=False)
for name, value, color in zip(cagrs.keys(), cagrs.values(), [NAVY, RED, TEAL]):
    ax2.hlines(name, 0, value * 100, color=color, linewidth=5, alpha=0.8)
    ax2.scatter(value * 100, name, s=100, color=color, zorder=3)
    ax2.text(value * 100 + 1.5, name, f"{value:.1%}", va="center", fontsize=10, weight="bold")
ax2.axvline(0, color="#777777", linewidth=0.8)
ax2.set_xlabel("Three-year compound annual growth rate (%)")
ax2.set_title("FY2022–FY2025 CAGR bridge")
ax2.set_xlim(0, max(cagrs.values()) * 120)
fig.suptitle("Growth velocity: earnings and cash flow outpaced a 27% revenue CAGR", fontsize=14, weight="bold")
finish_figure(
    fig, "figure_02_growth.png",
    "Source: Yahoo Finance annual statements; author calculations. Currency: USD. Units: US$ billions and CAGR
percent. Period: FY2022–FY2025."
)
```

Page 19 

ANET | Investment Identification Report 

##### **Code cell 6** 

```
# Figure 3 - Capital structure and solvency
fig, ax = plt.subplots(figsize=(10.8, 5.8))
x = np.arange(len(fy))
w = 0.24
b1 = ax.bar(x - w, fund["Cash & Short Investments"] / 1e9, w, color=TEAL, label="Cash & short investments")
b2 = ax.bar(x, fund["Equity"] / 1e9, w, color=NAVY, label="Equity")
b3 = ax.bar(x + w, fund["Total Debt"] / 1e9, w, color=RED, label="Debt")
ax.plot(x, fund["Net Cash"] / 1e9, color=GOLD, marker="D", linewidth=2.4, label="Net cash")
ax.set_xticks(x, fy)
ax.set_ylabel("US$ billions")
ax.set_title("Capital structure: a growing net-cash buffer limits solvency risk")
ax.legend(ncol=2, frameon=False, loc="upper left")
for bars in (b1, b2):
    ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
for i, val in enumerate(fund["Debt / Equity"].fillna(0)):
    ax.text(i, -0.55, f"D/E {val:.2%}", ha="center", fontsize=8, color=SLATE)
ax.set_ylim(-1.0, max((fund["Equity"] / 1e9).max() * 1.2, 1))
finish_figure(
    fig, "figure_03_capital_structure.png",
    "Source: Yahoo Finance annual balance sheets; author calculations. Currency: USD. Units: US$ billions and
debt/equity percent. Period: FY2022–FY2025."
```

```
)
```

##### **Code cell 7** 

```
# Figure 4 - Liquidity and cash-flow quality
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 5.6))
ax1.plot(fy, fund["Current Ratio"], color=NAVY, marker="o", linewidth=2.5, label="Current ratio")
ax1.plot(fy, fund["Quick Ratio"], color=TEAL, marker="s", linewidth=2.5, label="Quick ratio")
ax1.axhline(1, color=RED, linestyle="--", linewidth=1, label="1.0× floor")
ax1.set_ylabel("Multiple (×)")
ax1.set_title("Liquidity headroom")
ax1.legend(frameon=False)
x = np.arange(len(fy))
w = 0.28
ax2.bar(x - w/2, fund["Net Income"] / 1e9, w, color=SLATE, label="Net income")
ax2.bar(x + w/2, fund["Operating Cash Flow"] / 1e9, w, color=GREEN, label="Operating cash flow")
ax2.set_xticks(x, fy)
```

```
ax2.set_ylabel("US$ billions")
ax2.set_title("Cash conversion of accounting earnings")
ax2.legend(frameon=False, loc="upper left")
ax2b = ax2.twinx()
ax2b.plot(x, fund["CFO / Net Income"], color=GOLD, marker="D", linewidth=2.2)
ax2b.axhline(1, color=GOLD, linestyle=":", linewidth=1)
ax2b.set_ylabel("CFO / net income (×)")
```

```
fig.suptitle("Liquidity and cash-flow quality: ample coverage with conversion above 1× in FY2025", fontsize=14,
weight="bold")
finish_figure(
    fig, "figure_04_liquidity_cashflow.png",
    "Source: Yahoo Finance annual statements; author calculations. Currency: USD. Units: ratios (×) and US$
billions. Period: FY2022–FY2025."
```

```
)
```

##### **Code cell 8** 

```
peer_symbols = ["ANET", "CSCO", "HPE", "FFIV"]
peer_rows = []
```

```
for symbol in peer_symbols:
```

Page 20 

ANET | Investment Identification Report 

```
    peer_info = yf.Ticker(symbol).info
    peer_rows.append({
        "Ticker": symbol,
        "Forward P/E (x)": peer_info.get("forwardPE"),
        "EV / Revenue (x)": peer_info.get("enterpriseToRevenue"),
        "Revenue Growth (%)": (peer_info.get("revenueGrowth") or np.nan) * 100,
        "Net Margin (%)": (peer_info.get("profitMargins") or np.nan) * 100,
        "Market Cap (US$bn)": (peer_info.get("marketCap") or np.nan) / 1e9,
    })
peers = pd.DataFrame(peer_rows).dropna(subset=["Forward P/E (x)", "Revenue Growth (%)"])
peers.to_csv(ROOT / "peer_valuation_snapshot.csv", index=False)
display(peers.round(2))
fig, ax = plt.subplots(figsize=(10.2, 6.1))
sizes = np.clip(np.sqrt(peers["Market Cap (US$bn)"]) * 85, 180, 1350)
scatter = ax.scatter(
    peers["Forward P/E (x)"], peers["Revenue Growth (%)"],
    s=sizes, c=peers["Net Margin (%)"], cmap="viridis", alpha=0.82,
    edgecolor="white", linewidth=1.4,
)
for _, r in peers.iterrows():
    ax.annotate(r["Ticker"], (r["Forward P/E (x)"], r["Revenue Growth (%)"]),
                xytext=(7, 7), textcoords="offset points", fontsize=10, weight="bold")
ax.set_xlabel("Forward price/earnings (×)")
ax.set_ylabel("Latest year-on-year revenue growth (%)")
ax.set_title("Valuation-growth map: ANET's premium is supported by superior growth and margin")
cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
cbar.set_label("Net margin (%)")
snapshot_date = anet_px.index.max().strftime("%d %b %Y")
finish_figure(
    fig, "figure_05_valuation.png",
    f"Source: Yahoo Finance company snapshots. Currency: USD. Units: multiples (×), percent and US$bn bubble size.
Period: snapshot {snapshot_date}; forward/trailing fields."
)
```

##### **Code cell 9** 

```
tech = anet_px[["Adj Close", "Close", "Volume"]].copy()
tech["SMA50"] = tech["Adj Close"].rolling(50).mean()
tech["SMA200"] = tech["Adj Close"].rolling(200).mean()
tech["EMA12"] = tech["Adj Close"].ewm(span=12, adjust=False).mean()
tech["EMA26"] = tech["Adj Close"].ewm(span=26, adjust=False).mean()
tech["MACD"] = tech["EMA12"] - tech["EMA26"]
tech["MACD Signal"] = tech["MACD"].ewm(span=9, adjust=False).mean()
tech["BB Mid"] = tech["Adj Close"].rolling(20).mean()
tech["BB Std"] = tech["Adj Close"].rolling(20).std()
tech["BB Upper"] = tech["BB Mid"] + 2 * tech["BB Std"]
tech["BB Lower"] = tech["BB Mid"] - 2 * tech["BB Std"]
```

```
delta = tech["Adj Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.nan)
tech["RSI14"] = 100 - (100 / (1 + rs))
tech.to_csv(ROOT / "anet_technical_indicators.csv")
```

Page 21 

ANET | Investment Identification Report 

```
latest = tech.dropna().iloc[-1]
technical_snapshot = pd.DataFrame({
```

```
    "Metric": ["Adjusted close", "SMA50", "SMA200", "Bollinger upper", "Bollinger lower", "RSI(14)", "MACD", "MACD
signal"],
```

```
    "Value": [latest["Adj Close"], latest["SMA50"], latest["SMA200"], latest["BB Upper"], latest["BB Lower"],
latest["RSI14"], latest["MACD"], latest["MACD Signal"]],
})
display(technical_snapshot.round(2))
```

##### **Code cell 10** 

```
# Figure 6 - Trend architecture
view = tech.loc[tech.index >= tech.index.max() - pd.DateOffset(years=3)]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.4, 7.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
ax1.plot(view.index, view["Adj Close"], color=NAVY, linewidth=1.5, label="Adjusted close")
ax1.plot(view.index, view["SMA50"], color=TEAL, linewidth=1.8, label="50-day SMA")
ax1.plot(view.index, view["SMA200"], color=GOLD, linewidth=2.1, label="200-day SMA")
ax1.fill_between(view.index, view["SMA50"], view["SMA200"],
```

```
                 where=(view["SMA50"] >= view["SMA200"]), color=GREEN, alpha=0.08)
ax1.set_ylabel("Adjusted price (US$ per share)")
ax1.set_title("Trend architecture: price, medium-term momentum and long-term regime")
ax1.legend(frameon=False, ncol=3)
vol_m = view["Volume"] / 1e6
ax2.bar(view.index, vol_m, width=2.2, color=np.where(view["Adj Close"].diff() >= 0, TEAL, RED), alpha=0.55)
ax2.plot(view.index, vol_m.rolling(20).mean(), color=NAVY, linewidth=1.2, label="20-day average volume")
ax2.set_ylabel("Volume (m shares)")
ax2.legend(frameon=False, loc="upper left")
finish_figure(
    fig, "figure_06_moving_averages.png",
```

```
    f"Source: Yahoo Finance adjusted daily prices. Currency: USD. Units: US$/share and million shares. Period:
{view.index.min():%d %b %Y}–{view.index.max():%d %b %Y}."
)
```

##### **Code cell 11** 

```
# Figure 7 - Bollinger/RSI risk map
view1 = tech.loc[tech.index >= tech.index.max() - pd.DateOffset(years=1)]
```

```
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.4, 7.4), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
ax1.plot(view1.index, view1["Adj Close"], color=NAVY, linewidth=1.5, label="Adjusted close")
ax1.plot(view1.index, view1["BB Mid"], color=GOLD, linewidth=1.3, label="20-day mean")
ax1.plot(view1.index, view1["BB Upper"], color=SLATE, linewidth=0.8)
ax1.plot(view1.index, view1["BB Lower"], color=SLATE, linewidth=0.8)
ax1.fill_between(view1.index, view1["BB Lower"], view1["BB Upper"], color=CYAN, alpha=0.13, label="±2σ band")
ax1.set_ylabel("Adjusted price (US$ per share)")
ax1.set_title("Volatility envelope and momentum regime")
ax1.legend(frameon=False, ncol=3)
ax2.plot(view1.index, view1["RSI14"], color=TEAL, linewidth=1.4)
ax2.fill_between(view1.index, 70, 100, color=RED, alpha=0.08)
ax2.fill_between(view1.index, 0, 30, color=GREEN, alpha=0.08)
ax2.axhline(70, color=RED, linestyle="--", linewidth=1)
ax2.axhline(50, color=SLATE, linestyle=":", linewidth=1)
ax2.axhline(30, color=GREEN, linestyle="--", linewidth=1)
ax2.set_ylim(0, 100)
```

```
ax2.set_ylabel("RSI(14)")
finish_figure(
```

```
    fig, "figure_07_bollinger_rsi.png",
```

```
    f"Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: US$/share, standard
deviations and RSI index (0–100). Period: {view1.index.min():%d %b %Y}–{view1.index.max():%d %b %Y}."
)
```

Page 22 

ANET | Investment Identification Report 

##### **Code cell 12** 

```
adj_name = "Adj Close"
returns = pd.concat({
    "ANET": anet_px[adj_name].pct_change(),
    "Market": market_px[adj_name].pct_change(),
    "XLK": sector_px[adj_name].pct_change(),
    "TBillAnnualPct": rf_px[adj_name],
}, axis=1).dropna()
returns["RfDaily"] = (returns["TBillAnnualPct"] / 100) / 252
returns["ANET Excess"] = returns["ANET"] - returns["RfDaily"]
returns["Market Excess"] = returns["Market"] - returns["RfDaily"]
```

```
X = sm.add_constant(returns["Market Excess"])
capm_model = sm.OLS(returns["ANET Excess"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
alpha_daily = capm_model.params["const"]
beta = capm_model.params["Market Excess"]
alpha_annual = (1 + alpha_daily) ** 252 - 1
capm_metrics = {
    "observations": int(capm_model.nobs),
    "start": returns.index.min().strftime("%Y-%m-%d"),
    "end": returns.index.max().strftime("%Y-%m-%d"),
    "alpha_daily": float(alpha_daily),
    "alpha_annual": float(alpha_annual),
    "alpha_pvalue": float(capm_model.pvalues["const"]),
    "beta": float(beta),
    "beta_pvalue": float(capm_model.pvalues["Market Excess"]),
    "r_squared": float(capm_model.rsquared),
    "risk_free_latest_pct": float(returns["TBillAnnualPct"].iloc[-1]),
```

```
}
display(pd.DataFrame([capm_metrics]).T.rename(columns={0: "CAPM result"}))
print(capm_model.summary())
```

```
sample = returns.sample(min(900, len(returns)), random_state=42).sort_values("Market Excess")
pred = capm_model.params["const"] + capm_model.params["Market Excess"] * sample["Market Excess"]
fig, ax = plt.subplots(figsize=(10.5, 6.2))
```

```
ax.scatter(sample["Market Excess"] * 100, sample["ANET Excess"] * 100,
```

```
           s=14, alpha=0.28, color=TEAL, edgecolor="none", label="Daily observations")
```

```
ax.plot(sample["Market Excess"] * 100, pred * 100, color=RED, linewidth=2.4,
```

```
        label=f"OLS-HAC fit: β={beta:.2f}, annualised α={alpha_annual:.1%}")
```

```
ax.axhline(0, color=SLATE, linewidth=0.6)
```

```
ax.axvline(0, color=SLATE, linewidth=0.6)
ax.set_xlabel("S&P 500 daily excess return (%)")
ax.set_ylabel("ANET daily excess return (%)")
ax.set_title("CAPM security characteristic line with Newey–West inference")
ax.legend(frameon=False)
finish_figure(
    fig, "figure_08_capm_regression.png",
```

```
    f"Source: Yahoo Finance adjusted daily prices and 13-week T-bill yield; author OLS-HAC regression. Currency:
USD. Units: daily excess return percent. Period: {returns.index.min():%d %b %Y}–{returns.index.max():%d %b %Y}."
)
```

##### **Code cell 13** 

```
def performance_stats(series, rf_daily):
    series = series.dropna()
    wealth = (1 + series).cumprod()
    years_elapsed = (series.index[-1] - series.index[0]).days / 365.25
```

```
    excess = series - rf_daily.reindex(series.index).ffill().fillna(0)
```

Page 23 

ANET | Investment Identification Report 

```
    return {
        "Total Return": wealth.iloc[-1] - 1,
        "CAGR": wealth.iloc[-1] ** (1 / years_elapsed) - 1,
        "Annual Volatility": series.std() * np.sqrt(252),
        "Sharpe": excess.mean() / excess.std() * np.sqrt(252),
        "Maximum Drawdown": (wealth / wealth.cummax() - 1).min(),
    }
```

```
perf = pd.DataFrame({
    "ANET": performance_stats(returns["ANET"], returns["RfDaily"]),
    "S&P 500": performance_stats(returns["Market"], returns["RfDaily"]),
    "XLK": performance_stats(returns["XLK"], returns["RfDaily"]),
}).T
perf.to_csv(ROOT / "benchmark_performance.csv")
display(perf.style.format({
    "Total Return": "{:.1%}", "CAGR": "{:.1%}", "Annual Volatility": "{:.1%}",
    "Sharpe": "{:.2f}", "Maximum Drawdown": "{:.1%}"
}))
```

```
wealth = (1 + returns[["ANET", "Market", "XLK"]]).cumprod() * 100
wealth = wealth.rename(columns={"Market": "S&P 500"})
drawdown = wealth / wealth.cummax() - 1
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.4, 7.6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
colors = {"ANET": TEAL, "S&P 500": NAVY, "XLK": GOLD}
for col in wealth:
    ax1.plot(wealth.index, wealth[col], label=col, color=colors[col], linewidth=2 if col == "ANET" else 1.5)
    ax2.plot(drawdown.index, drawdown[col] * 100, label=col, color=colors[col], linewidth=1.2)
ax1.set_ylabel("Growth of US$100 (US$)")
ax1.set_yscale("log")
ax1.set_title("Benchmark-relative wealth: log scale preserves proportional comparison")
ax1.legend(frameon=False, ncol=3)
ax2.set_ylabel("Drawdown (%)")
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.axhline(0, color=SLATE, linewidth=0.6)
finish_figure(
    fig, "figure_09_benchmark_drawdown.png",
    f"Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: growth of US$100 (log
scale) and drawdown percent. Period: {returns.index.min():%d %b %Y}–{returns.index.max():%d %b %Y}."
)
```

##### **Code cell 14** 

```
# Figure 10 - Monthly return heatmap, a compact view of timing risk
monthly = (1 + returns["ANET"]).resample("ME").prod() - 1
monthly_df = monthly.to_frame("Return")
monthly_df["Year"] = monthly_df.index.year
monthly_df["Month"] = monthly_df.index.month
heat = monthly_df.pivot(index="Year", columns="Month", values="Return") * 100
heat =
```

```
heat.rename(columns={1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"D
ec"})
fig, ax = plt.subplots(figsize=(11.2, 5.1))
sns.heatmap(heat, annot=True, fmt=".1f", cmap="RdYlGn", center=0, linewidths=0.5,
            cbar_kws={"label": "Monthly return (%)"}, ax=ax)
ax.set_title("ANET monthly return heatmap: strong compounding includes episodic losses")
ax.set_xlabel("")
ax.set_ylabel("")
finish_figure(
```

Page 24 

ANET | Investment Identification Report 

```
    fig, "figure_10_monthly_heatmap.png",
```

```
    f"Source: Yahoo Finance adjusted daily prices; author calculations. Currency: USD. Units: monthly total return
percent. Period: {monthly.index.min():%b %Y}–{monthly.index.max():%b %Y}."
)
```

##### **Code cell 15** 

```
current_price = float(info.get("currentPrice") or anet_px["Close"].iloc[-1])
forward_eps = float(info.get("forwardEps") or info.get("trailingEps"))
scenario = pd.DataFrame({
    "Scenario": ["Bear", "Base", "Bull"],
    "Probability": [0.25, 0.50, 0.25],
    "Next-year EPS growth": [0.12, 0.20, 0.28],
    "Terminal P/E": [30.0, 35.0, 42.0],
})
scenario["Implied price"] = forward_eps * (1 + scenario["Next-year EPS growth"]) * scenario["Terminal P/E"]
scenario["Upside / downside"] = scenario["Implied price"] / current_price - 1
expected_price = float((scenario["Probability"] * scenario["Implied price"]).sum())
expected_upside = expected_price / current_price - 1
scenario.to_csv(ROOT / "valuation_scenarios.csv", index=False)
display(scenario.style.format({
    "Probability": "{:.0%}", "Next-year EPS growth": "{:.0%}",
    "Terminal P/E": "{:.1f}×", "Implied price": "US${:.2f}", "Upside / downside": "{:+.1%}",
}))
```

```
score = 0
```

```
score += 1 if latest["Adj Close"] > latest["SMA200"] else -1
score += 1 if latest["SMA50"] > latest["SMA200"] else -1
score += 1 if latest["MACD"] > latest["MACD Signal"] else -1
score += 0 if 30 <= latest["RSI14"] <= 70 else -1
technical_regime = "constructive" if score >= 2 else ("mixed" if score >= 0 else "cautious")
recommendation = "STAGED ACCUMULATE" if expected_upside >= 0.08 else "WATCH / BUY ON WEAKNESS"
```

###### `results = {` 

```
    "company": "Arista Networks, Inc.",
    "ticker": TICKER,
    "price_start": anet_px.index.min().strftime("%Y-%m-%d"),
    "price_end": anet_px.index.max().strftime("%Y-%m-%d"),
    "fundamental_start_year": int(fund.index.min().year),
    "fundamental_end_year": int(fund.index.max().year),
    "current_price": current_price,
    "market_cap": float(info.get("marketCap") or np.nan),
    "enterprise_value": float(info.get("enterpriseValue") or np.nan),
    "forward_pe": float(info.get("forwardPE") or np.nan),
    "trailing_pe": float(info.get("trailingPE") or np.nan),
    "ev_revenue": float(info.get("enterpriseToRevenue") or np.nan),
    "ev_ebitda": float(info.get("enterpriseToEbitda") or np.nan),
    "forward_eps": forward_eps,
    "analyst_target_mean": float(info.get("targetMeanPrice") or np.nan),
    "analyst_opinions": int(info.get("numberOfAnalystOpinions") or 0),
    "revenue_latest": float(fund["Revenue"].iloc[-1]),
    "net_income_latest": float(fund["Net Income"].iloc[-1]),
    "fcf_latest": float(fund["Free Cash Flow"].iloc[-1]),
    "revenue_cagr": float(cagrs["Revenue"]),
    "net_income_cagr": float(cagrs["Net income"]),
    "fcf_cagr": float(cagrs["Free cash flow"]),
    "gross_margin_latest": float(fund["Gross Margin"].iloc[-1]),
    "operating_margin_latest": float(fund["Operating Margin"].iloc[-1]),
```

Page 25 

ANET | Investment Identification Report 

```
    "net_margin_latest": float(fund["Net Margin"].iloc[-1]),
    "net_cash_latest": float(fund["Net Cash"].iloc[-1]),
    "debt_equity_latest": float(fund["Debt / Equity"].iloc[-1]),
    "current_ratio_latest": float(fund["Current Ratio"].iloc[-1]),
    "quick_ratio_latest": float(fund["Quick Ratio"].iloc[-1]),
    "cfo_net_income_latest": float(fund["CFO / Net Income"].iloc[-1]),
    "fcf_net_income_latest": float(fund["FCF / Net Income"].iloc[-1]),
    "latest_adjusted_close": float(latest["Adj Close"]),
    "sma50": float(latest["SMA50"]),
    "sma200": float(latest["SMA200"]),
    "rsi14": float(latest["RSI14"]),
    "bollinger_upper": float(latest["BB Upper"]),
    "bollinger_lower": float(latest["BB Lower"]),
    "macd": float(latest["MACD"]),
    "macd_signal": float(latest["MACD Signal"]),
    "technical_score": int(score),
    "technical_regime": technical_regime,
    "recommendation": recommendation,
    "expected_price": expected_price,
    "expected_upside": expected_upside,
    "capm": capm_metrics,
    "performance": perf.to_dict(orient="index"),
    "figures": [f"figure_{i:02d}_{name}.png" for i, name in [
        (1,"profitability"),(2,"growth"),(3,"capital_structure"),(4,"liquidity_cashflow"),
        (5,"valuation"),(6,"moving_averages"),(7,"bollinger_rsi"),(8,"capm_regression"),
        (9,"benchmark_drawdown"),(10,"monthly_heatmap")
    ]],
}
with open(ROOT / "analysis_results.json", "w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=2, allow_nan=False)
```

```
display(Markdown(
    f"### Decision: **{recommendation}**  \n"
    f"Evidence-weighted 12-month value: **US${expected_price:,.2f}** "
    f"({expected_upside:+.1%} versus US${current_price:,.2f}); "
    f"technical regime: **{technical_regime}**."
))
```

Page 26 

