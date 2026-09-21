"""
Definitions the app can stand behind.

Why a glossary and not just search
----------------------------------
The course corpus teaches; it does not define. Ask it "what is compounding?"
and the three best-matching passages are about how a SIP compounds, how
compounding works against you on a credit card, and why time matters — all
correct, none a definition. Handed those, the local model answered that
compounding is "new money entering the market continuously", which is not what
the word means.

The failure is structural. Teaching material explains a term in use, and no
retrieval trick turns that into a definition. So the definitions are written
here, and "what is X" is answered from this before anything else is tried.

Everything below is plain enough for a beginner and specific to India where that
matters — rupees, Nifty, CIBIL, the actual section numbers. ``example`` carries
a concrete number wherever a number makes the idea land, because "interest on
interest" means nothing until you see it become a figure.

Nothing here is generated. If a term is missing, the app says the course does
not cover it rather than inventing an entry.
"""

from __future__ import annotations

# term -> (definition, example, aliases)
TERMS: dict[str, dict] = {
    # ---------------------------------------------------------------- money --
    'compounding': {
        'definition': 'Earning returns on your past returns, not just on what you put in. '
                      'Each year starts from a bigger base than the last, so growth speeds up the longer you leave it.',
        'example': 'Rs 1,00,000 at 10% becomes Rs 1,10,000 after a year. The second year earns 10% on '
                   'Rs 1,10,000, not on Rs 1,00,000 — Rs 11,000 instead of Rs 10,000. After 20 years it is '
                   'about Rs 6,72,000, and only Rs 2,00,000 of that is interest on the original amount.',
        'aliases': ('compound interest', 'compounding effect', 'power of compounding'),
    },
    'simple interest': {
        'definition': 'Interest calculated only on the original amount, never on the interest already earned.',
        'example': 'Rs 1,00,000 at 10% simple interest pays Rs 10,000 every year, forever. '
                   'Compound interest on the same money pays more each year.',
        'aliases': (),
    },
    'inflation': {
        'definition': 'The rate at which prices rise, which is the rate at which money loses buying power. '
                      'It is why money left in a savings account shrinks in real terms.',
        'example': 'At 6% inflation, something costing Rs 100 today costs about Rs 180 in ten years. '
                   'A savings account paying 3% loses you 3% of buying power a year.',
        'aliases': ('inflation rate',),
    },
    'real return': {
        'definition': 'Your return after subtracting inflation. It is the only return that tells you '
                      'whether you can actually buy more than before.',
        'example': 'A fixed deposit paying 7% while inflation runs at 6% has a real return of about 1%.',
        'aliases': ('real rate of return', 'inflation-adjusted return'),
    },
    'emergency fund': {
        'definition': 'Money set aside purely to cover a sudden loss of income or an unavoidable bill, '
                      'kept somewhere you can reach within a day. Usually three to six months of expenses.',
        'example': 'If you spend Rs 40,000 a month, an emergency fund is roughly Rs 1.2 to Rs 2.4 lakh, '
                   'in a savings account or liquid fund — never in stocks, because emergencies do not wait '
                   'for the market to recover.',
        'aliases': ('rainy day fund', 'contingency fund'),
    },
    'net worth': {
        'definition': 'Everything you own minus everything you owe. The single number that says whether '
                      'a year went well.',
        'example': 'Rs 12 lakh in savings and investments, minus a Rs 4 lakh car loan, is a net worth of Rs 8 lakh.',
        'aliases': (),
    },
    'liquidity': {
        'definition': 'How quickly something can become spendable cash without losing value in the process.',
        'example': 'A savings account is highly liquid. Property is not — selling it takes months and costs fees.',
        'aliases': ('liquid',),
    },
    'budget': {
        'definition': 'A plan for where income goes before it arrives, so saving is a decision rather than '
                      'whatever happens to be left over.',
        'example': 'The 50/30/20 split: half to needs, 30% to wants, 20% to saving and repaying debt.',
        'aliases': ('budgeting',),
    },

    # ------------------------------------------------------------ investing --
    'index fund': {
        'definition': 'A fund that simply holds every company in an index, in proportion to size, '
                      'instead of paying someone to pick stocks. Low cost is the whole point.',
        'example': 'A Nifty 50 index fund holds all 50 companies and charges roughly 0.2% a year, '
                   'against about 1.8% for an actively managed fund. Over ten years most active large-cap '
                   'funds fail to beat the index after fees.',
        'aliases': ('index funds', 'passive fund', 'nifty index fund'),
    },
    'mutual fund': {
        'definition': 'A pool of money from many investors, managed together and invested in shares, bonds '
                      'or both. You own units of the pool rather than the underlying holdings directly.',
        'example': 'Put in Rs 10,000 when the unit price is Rs 50 and you own 200 units.',
        'aliases': ('mutual funds', 'fund'),
    },
    'etf': {
        'definition': 'An exchange-traded fund: a fund whose units trade on the stock exchange like a share, '
                      'so the price moves through the day. Most track an index, the same as an index fund — '
                      'the difference is how you buy it, not what it holds.',
        'example': 'A Nifty 50 ETF is bought through a broker at whatever it trades for right now. '
                   'An index fund is bought from the fund house at one price set after the market closes.',
        'aliases': ('exchange traded fund', 'exchange-traded fund'),
    },
    'sip': {
        'definition': 'A systematic investment plan: a fixed amount invested automatically every month, '
                      'whatever the price that month. It removes the decision of when to buy.',
        'example': 'Rs 5,000 on the 5th of each month buys more units when prices are low and fewer when '
                   'they are high, so your average cost is an actual average.',
        'aliases': ('systematic investment plan', 'sips'),
    },
    'lump sum': {
        'definition': 'Investing the whole amount at once instead of spreading it over months.',
        'example': 'In a steadily rising market a lump sum usually beats a SIP, because the money is '
                   'invested for longer. It also means one bad entry date affects everything.',
        'aliases': ('lumpsum', 'lump-sum'),
    },
    'rupee cost averaging': {
        'definition': 'The effect of investing a fixed amount regularly: you automatically buy more units '
                      'when prices fall and fewer when they rise.',
        'example': 'Rs 6,000 a month buys 60 units at Rs 100 and 100 units at Rs 60. The average price paid '
                   'is Rs 75, below the Rs 80 average of the two prices.',
        'aliases': ('cost averaging', 'dollar cost averaging'),
    },
    'nav': {
        'definition': 'Net asset value: the per-unit price of a mutual fund, worked out once a day after '
                      'the market closes. A low NAV does not make a fund cheap.',
        'example': 'A fund holding Rs 100 crore across 5 crore units has a NAV of Rs 20.',
        'aliases': ('net asset value',),
    },
    'expense ratio': {
        'definition': 'The percentage of your money a fund charges every year to run itself, taken out of '
                      'returns before you ever see them. Small differences compound into large ones.',
        'example': 'On Rs 10 lakh, 1.8% is Rs 18,000 a year against Rs 2,000 at 0.2%. Over 20 years that '
                   'gap costs several lakh in forgone growth.',
        'aliases': ('ter', 'total expense ratio'),
    },
    'exit load': {
        'definition': 'A fee charged for selling fund units before a set period, meant to discourage '
                      'short-term money.',
        'example': 'A 1% exit load before one year costs Rs 1,000 on a Rs 1 lakh redemption.',
        'aliases': (),
    },
    'direct plan': {
        'definition': 'The version of a mutual fund bought straight from the fund house, with no '
                      'distributor commission built into the expense ratio.',
        'example': 'The same fund often costs about 1% less a year as a direct plan than as a regular plan. '
                   'It is the identical portfolio.',
        'aliases': ('direct vs regular', 'regular plan'),
    },
    'asset allocation': {
        'definition': 'How your money is split across kinds of asset — equity, debt, gold, cash. It decides '
                      'most of your risk, far more than which particular fund or stock you pick.',
        'example': 'A 60/40 split means 60% in equity and 40% in debt. In a year equity falls 30%, that '
                   'portfolio falls about 18%, not 30%.',
        'aliases': ('allocation',),
    },
    'diversification': {
        'definition': 'Spreading money across things that do not all fall at once. It lowers risk without '
                      'requiring you to predict which one will do well.',
        'example': 'Five IT stocks is not diversification — one sector shock moves all five. IT, banking, '
                   'pharma and some debt is.',
        'aliases': ('diversify', 'diversified'),
    },
    'equity': {
        'definition': 'Ownership in a business. Shares are equity, and so is an equity mutual fund that '
                      'holds them.',
        'example': 'Equity has the highest long-run return and the largest falls along the way, which is '
                   'why it suits money you will not need for years.',
        'aliases': ('equities', 'shares', 'stock', 'share'),
    },
    'debt fund': {
        'definition': 'A fund that lends rather than owns — government and corporate bonds. Steadier than '
                      'equity and lower returning.',
        'example': 'Used for money needed in one to three years, where a 30% equity fall would be ruinous.',
        'aliases': ('debt funds', 'bond fund'),
    },
    'bond': {
        'definition': 'A loan to a government or company that pays fixed interest and returns the principal '
                      'on a set date.',
        'example': 'Bond prices fall when interest rates rise, because newer bonds pay more.',
        'aliases': ('bonds',),
    },
    'gold': {
        'definition': 'Held as ballast rather than growth: it often holds value when equity falls, and it '
                      'produces no income of its own.',
        'example': 'Usually 5-10% of a portfolio. Sovereign gold bonds also pay 2.5% a year on top of the '
                   'gold price, which physical gold does not.',
        'aliases': ('sovereign gold bond', 'sgb'),
    },
    'aum': {
        'definition': 'Assets under management: the total money a fund or fund house is looking after.',
        'example': 'A large AUM can make it harder for a small-cap fund to buy and sell without moving prices.',
        'aliases': ('assets under management',),
    },

    # ---------------------------------------------------------------- stocks --
    'share': {
        'definition': 'One unit of ownership in a company. Owning it makes you entitled to a slice of the '
                      'profits and the losses.',
        'example': 'A company with 1 crore shares and Rs 50 crore of profit earned Rs 50 per share.',
        'aliases': ('stocks', 'shares', 'scrip'),
    },
    'market cap': {
        'definition': 'The whole company\'s price: share price multiplied by number of shares. It is how '
                      'companies are sorted into large, mid and small cap.',
        'example': 'Rs 500 a share across 10 crore shares is a market cap of Rs 5,000 crore.',
        'aliases': ('market capitalisation', 'market capitalization', 'marketcap'),
    },
    'large cap': {
        'definition': 'The 100 biggest listed companies by market value. Steadier, slower-growing, and the '
                      'usual starting point.',
        'example': 'Most Nifty 50 companies are large caps.',
        'aliases': ('largecap', 'mid cap', 'midcap', 'small cap', 'smallcap'),
    },
    'p/e ratio': {
        'definition': 'Price divided by earnings per share: how many rupees you pay for one rupee of annual '
                      'profit. Useful for comparing similar companies, meaningless across different industries.',
        'example': 'A share at Rs 500 earning Rs 25 has a P/E of 20 — twenty years of current profit to pay '
                   'back the price.',
        'aliases': ('pe ratio', 'price to earnings', 'price-to-earnings'),
    },
    'dividend': {
        'definition': 'Cash a company pays out of profit to its shareholders. It is not free money — the '
                      'share price drops by roughly the amount paid.',
        'example': 'A Rs 10 dividend on a Rs 400 share is a 2.5% dividend yield.',
        'aliases': ('dividends', 'dividend yield'),
    },
    'ipo': {
        'definition': 'An initial public offering: the first time a company sells shares to the public and '
                      'lists on an exchange.',
        'example': 'Listing-day gains get the attention; a large share of IPOs trade below their issue price '
                   'a year later.',
        'aliases': ('initial public offering',),
    },
    'bull market': {
        'definition': 'A long stretch of rising prices and confident buying.',
        'example': 'Bull markets make risky portfolios look skilful, which is when concentration builds up.',
        'aliases': ('bull run', 'bear market', 'bearish', 'bullish'),
    },
    'volatility': {
        'definition': 'How much a price swings around, up or down. High volatility means large moves in '
                      'both directions, not just falls.',
        'example': 'A stock moving 3% most days is far more volatile than one moving 0.5%, and needs a '
                   'smaller position for the same risk.',
        'aliases': ('volatile',),
    },
    'beta': {
        'definition': 'How much a stock tends to move when the whole market moves. Above 1 amplifies the '
                      'market, below 1 dampens it.',
        'example': 'A beta of 1.4 means roughly a 1.4% move for every 1% the index moves.',
        'aliases': (),
    },
    'drawdown': {
        'definition': 'The fall from a portfolio\'s highest point to its lowest before it recovers. The '
                      'number that decides whether you can actually hold on.',
        'example': 'A 50% drawdown needs a 100% gain to get back to even.',
        'aliases': ('max drawdown', 'maximum drawdown'),
    },
    'stop loss': {
        'definition': 'A standing instruction to sell if the price falls to a set level, deciding the exit '
                      'before emotion is involved.',
        'example': 'Buying at Rs 500 with a stop at Rs 450 caps the loss near 10%.',
        'aliases': ('stop-loss', 'stoploss'),
    },
    'limit order': {
        'definition': 'An order to buy or sell only at a price you name or better. It may not execute at all.',
        'example': 'A market order fills immediately at whatever the price is; a limit order waits for yours.',
        'aliases': ('market order',),
    },
    'nifty 50': {
        'definition': 'India\'s main stock index: the 50 largest, most traded companies on the NSE, weighted '
                      'by size. Used as the benchmark most funds are measured against.',
        'example': 'When the news says "the market rose 1%", it usually means the Nifty or the Sensex.',
        'aliases': ('nifty', 'sensex', 'index'),
    },
    'demat account': {
        'definition': 'The account that holds your shares electronically, the way a bank account holds money.',
        'example': 'You need a demat account plus a trading account to buy shares in India.',
        'aliases': ('demat', 'trading account'),
    },
    'portfolio': {
        'definition': 'Everything you hold, considered as one thing. Risk lives at the portfolio level, not '
                      'in any single holding.',
        'example': 'Four excellent bank stocks can still be a badly built portfolio.',
        'aliases': (),
    },

    # ------------------------------------------------------------------ debt --
    'credit score': {
        'definition': 'A number from 300 to 900 summarising how reliably you have repaid borrowed money. '
                      'Lenders use it to decide whether to lend and at what rate.',
        'example': 'Above 750 usually gets the advertised rate. Paying on time and keeping card balances '
                   'low are the two things that move it most.',
        'aliases': ('cibil', 'cibil score', 'credit rating'),
    },
    'credit utilisation': {
        'definition': 'The share of your credit limit you are using. High utilisation lowers your score even '
                      'when you pay in full every month.',
        'example': 'Spending Rs 90,000 on a Rs 1 lakh limit is 90% utilisation. Below 30% is the usual advice.',
        'aliases': ('credit utilization',),
    },
    'emi': {
        'definition': 'Equated monthly instalment: the fixed monthly payment on a loan, covering interest '
                      'first and principal second.',
        'example': 'Early EMIs are mostly interest. On a 20-year home loan, the first year barely reduces '
                   'what you owe.',
        'aliases': ('equated monthly instalment', 'equated monthly installment'),
    },
    'principal': {
        'definition': 'The amount actually borrowed or invested, before any interest.',
        'example': 'A Rs 20 lakh home loan has a principal of Rs 20 lakh; over 20 years you may repay close '
                   'to double that in total.',
        'aliases': (),
    },
    'prepayment': {
        'definition': 'Paying off part of a loan early. It reduces the principal, so every future interest '
                      'charge is calculated on a smaller number.',
        'example': 'One extra EMI a year on a 20-year home loan can cut roughly four years off it.',
        'aliases': ('prepay', 'foreclosure'),
    },
    'tenure': {
        'definition': 'How long a loan or deposit runs for.',
        'example': 'A longer loan tenure lowers the EMI and raises the total interest paid.',
        'aliases': (),
    },

    # ------------------------------------------------------------- banking ---
    'fixed deposit': {
        'definition': 'Money locked with a bank for a set period at a rate agreed upfront. It cannot fall '
                      'in value, and it usually barely beats inflation.',
        'example': 'Rs 1 lakh at 7% for three years returns about Rs 1.22 lakh. Breaking it early cuts the rate.',
        'aliases': ('fd', 'term deposit'),
    },
    'recurring deposit': {
        'definition': 'A fixed deposit paid into monthly instead of all at once.',
        'example': 'Rs 5,000 a month for three years at 7% comes to roughly Rs 2 lakh.',
        'aliases': ('rd',),
    },

    # ---------------------------------------------------------------- tax -----
    'ltcg': {
        'definition': 'Long-term capital gains tax: what you pay on profit from assets held beyond the '
                      'long-term period — more than a year for listed shares and equity funds.',
        'example': 'Equity gains above the annual exempt limit are taxed at a lower rate than short-term gains.',
        'aliases': ('long term capital gains', 'long-term capital gains', 'capital gains'),
    },
    'stcg': {
        'definition': 'Short-term capital gains tax: the higher rate applied when you sell before the '
                      'long-term period is up.',
        'example': 'Selling an equity fund after eleven months is taxed noticeably harder than selling after '
                   'thirteen.',
        'aliases': ('short term capital gains', 'short-term capital gains'),
    },
    'section 80c': {
        'definition': 'The section of the Income Tax Act allowing certain investments and payments to be '
                      'deducted from taxable income, up to an annual cap, under the old regime.',
        'example': 'EPF, PPF, ELSS, term insurance premiums and home loan principal all count towards it.',
        'aliases': ('80c',),
    },
    'elss': {
        'definition': 'An equity-linked savings scheme: an equity mutual fund that qualifies for a Section '
                      '80C deduction and locks money in for three years.',
        'example': 'The shortest lock-in of the 80C options, and the only one that is fully equity.',
        'aliases': ('tax saving fund',),
    },
    'tds': {
        'definition': 'Tax deducted at source: tax withheld by whoever pays you, before the money arrives.',
        'example': 'A bank deducts TDS on fixed deposit interest above a threshold. It is an advance, not '
                   'an extra tax.',
        'aliases': ('tax deducted at source',),
    },

    # ----------------------------------------------------------- retirement --
    'ppf': {
        'definition': 'Public Provident Fund: a 15-year government-backed savings scheme with tax-free '
                      'interest and an 80C deduction.',
        'example': 'Safe and illiquid by design. Suited to money you genuinely will not touch.',
        'aliases': ('public provident fund',),
    },
    'epf': {
        'definition': 'Employees\' Provident Fund: retirement savings deducted from salary and matched by '
                      'the employer.',
        'example': 'For most salaried people it is the largest retirement holding they have and the one they '
                   'think about least.',
        'aliases': ("employees provident fund", 'provident fund'),
    },
    'nps': {
        'definition': 'National Pension System: a low-cost retirement account where you choose the equity '
                      'and debt mix, locked until retirement.',
        'example': 'Cheaper than most mutual funds, with an extra tax deduction beyond the 80C limit.',
        'aliases': ('national pension system',),
    },

    # ------------------------------------------------------------ insurance --
    'term insurance': {
        'definition': 'Pure life cover: it pays out if you die during the term and nothing if you do not. '
                      'That is why it is cheap.',
        'example': 'A Rs 1 crore cover for a healthy 30-year-old costs roughly Rs 10,000-15,000 a year. '
                   'Policies that "return" your premium cost several times more for the same cover.',
        'aliases': ('term plan', 'life insurance'),
    },
    'premium': {
        'definition': 'What you pay for an insurance policy, usually yearly.',
        'example': 'A higher deductible lowers the premium, because you are covering more of a claim yourself.',
        'aliases': (),
    },
    'deductible': {
        'definition': 'The part of a claim you pay before the insurer pays anything.',
        'example': 'On a Rs 50,000 hospital bill with a Rs 10,000 deductible, the insurer pays Rs 40,000.',
        'aliases': ('excess', 'co-pay', 'copay'),
    },

    # ------------------------------------------------------------ behaviour --
    'loss aversion': {
        'definition': 'Losses hurting more than equivalent gains please, which makes people hold losing '
                      'positions to avoid making the loss real.',
        'example': 'Selling a winner at 10% while holding a loser at 40% down is loss aversion, not strategy.',
        'aliases': ('loss averse',),
    },
    'recency bias': {
        'definition': 'Treating what happened recently as what happens generally.',
        'example': 'Buying whichever fund topped last year\'s table is recency bias, and last year\'s winner '
                   'is often next year\'s laggard.',
        'aliases': (),
    },
    'anchoring': {
        'definition': 'Fixing on one number — usually the price you paid — and judging everything against it, '
                      'even when it tells you nothing about what the thing is worth now.',
        'example': '"I will sell when it gets back to Rs 500" is anchoring to your entry price, which the '
                   'market has no knowledge of.',
        'aliases': ('anchor',),
    },
    'herd mentality': {
        'definition': 'Doing what everyone else is doing and treating the crowd\'s agreement as evidence.',
        'example': 'The crowd is most united at the top of a bubble and at the bottom of a crash.',
        'aliases': ('herding', 'fomo'),
    },
    'risk capacity': {
        'definition': 'How much loss your finances can actually absorb, decided by your income, your '
                      'commitments and how soon you need the money. Arithmetic, not temperament.',
        'example': 'Money needed in eighteen months has almost no risk capacity however brave you feel.',
        'aliases': ('risk tolerance', 'risk appetite'),
    },
}

# Alias -> canonical term, built once.
_LOOKUP: dict[str, str] = {}
for _term, _entry in TERMS.items():
    _LOOKUP[_term] = _term
    for _alias in _entry['aliases']:
        _LOOKUP.setdefault(_alias, _term)


def _normalise(text: str) -> str:
    """Strip the wrapping a question puts around the word being asked about."""
    cleaned = ' '.join((text or '').lower().split())
    for prefix in ('what is a ', 'what is an ', 'what is the ', 'what is ',
                   'what are ', 'what does ', 'define ', 'explain ',
                   'meaning of ', 'whats a ', 'whats an ', 'whats '):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    return cleaned.strip(' ?.!,:;"\'')


def look_up(term: str, *, fuzzy: bool = True) -> dict | None:
    """The entry for a term, or ``None``.

    Matches the term itself, its aliases, and the common ways a question wraps
    it — "what is an index fund?" resolves the same as "index fund".

    ``fuzzy`` also matches a term appearing anywhere in the text, which is what
    a highlighted phrase needs. Turn it off for questions: "why did my index
    fund drop 10% this week?" contains a term the glossary knows and is not a
    request for its definition.
    """
    cleaned = _normalise(term)
    if not cleaned:
        return None

    canonical = _LOOKUP.get(cleaned)

    # "expense ratio of this fund" still means expense ratio. Longest alias
    # first, so "credit score" is not shadowed by a shorter overlapping entry.
    if canonical is None and fuzzy:
        for alias in sorted(_LOOKUP, key=len, reverse=True):
            if len(alias) >= 4 and alias in cleaned:
                canonical = _LOOKUP[alias]
                break

    if canonical is None:
        return None

    entry = TERMS[canonical]
    return {
        'term': canonical,
        'definition': entry['definition'],
        'example': entry['example'],
    }


def defines(term: str) -> bool:
    """Whether the glossary covers a term."""
    return look_up(term) is not None


# Question openings that are asking about a term rather than about something
# that happened to it. "How big should my emergency fund be?" wants the entry;
# "Why did my index fund drop 10%?" mentions a term and wants something else.
ASKS_ABOUT = (
    'what is', 'what are', 'what does', 'whats', "what's", 'define', 'explain',
    'meaning of', 'how much', 'how big', 'how many', 'how long', 'how does',
    'how do', 'tell me about',
)


def asked_about(question: str) -> dict | None:
    """The entry a question is asking for, when it is asking for one.

    Wider than a strict lookup, because "how big should my emergency fund be?"
    is a question this glossary answers exactly — three to six months of
    expenses, with the rupee figure — and matching only the bare term misses it.
    Left to the model, that question produced "at least twice your monthly
    income" and a reference to a Federal Reserve calculator.

    Narrower than a fuzzy lookup, because the same fuzzy match would answer
    "why did my index fund drop?" with the definition of an index fund.
    """
    cleaned = ' '.join((question or '').lower().split()).strip(' ?.!')
    if not cleaned.startswith(ASKS_ABOUT):
        return None
    return look_up(question)
