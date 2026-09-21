"""
The Number Sense fact bank.

Each entry is a real, checkable figure with a note explaining why the magnitude
matters. A wrong guess should still leave the player knowing roughly the right
size of the thing, which is the whole point of the game: nobody needs the exact
rupee, everybody needs to know whether it is a thousand or a lakh.

Anything that drifts — rates, prices, thresholds — is marked so it can be
reviewed rather than silently going stale. Kept in its own module because a fact
bank is data, not logic, and it will grow.

Figures are as of the 2025-26 Indian financial year unless noted.
"""

ESTIMATE_FACTS: tuple[dict, ...] = (
    # ----- Rates and inflation ---------------------------------------------
    {
        'question': 'What is the RBI repo rate right now?',
        'answer': 5.5,
        'unit': '%',
        'context': 'The rate at which the RBI lends to commercial banks. It sets the floor for your loan rate.',
    },
    {
        'question': 'What is the long-run average inflation rate in India?',
        'answer': 6.0,
        'unit': '%',
        'context': 'At 6%, prices double roughly every 12 years. Cash left idle halves in purchasing power.',
    },
    {
        'question': 'What rate does a typical Indian savings account pay?',
        'answer': 3.0,
        'unit': '%',
        'context': 'Below inflation. Money parked in savings loses about 3% of its buying power a year.',
    },
    {
        'question': 'What does a one-year fixed deposit at a large Indian bank pay?',
        'answer': 6.8,
        'unit': '%',
        'context': 'Roughly matches inflation before tax, and falls below it after tax at higher slabs.',
    },
    {
        'question': 'What interest rate does a typical Indian credit card charge per year?',
        'answer': 42.0,
        'unit': '%',
        'context': 'Usually quoted as 3.5% a month, which sounds small and compounds to over 40%.',
    },
    {
        'question': 'What rate does a typical personal loan charge in India?',
        'answer': 13.0,
        'unit': '%',
        'context': 'Unsecured, so priced far above a home loan. Worth clearing before investing anywhere.',
    },
    {
        'question': 'What is the current rate on a Public Provident Fund account?',
        'answer': 7.1,
        'unit': '%',
        'context': 'Tax-free and government-backed, but locked for 15 years.',
    },
    {
        'question': 'What rate does the Employees Provident Fund credit each year?',
        'answer': 8.25,
        'unit': '%',
        'context': 'The best risk-free rate most salaried Indians have access to.',
    },
    {
        'question': 'What is a typical home loan rate in India today?',
        'answer': 8.5,
        'unit': '%',
        'context': 'The cheapest large borrowing available, because your house secures it.',
    },
    {
        'question': 'What annual return has the Nifty 50 delivered over the last 20 years?',
        'answer': 12.0,
        'unit': '%',
        'context': 'Before inflation. The real return is nearer 6%, and it arrived very unevenly.',
    },

    # ----- Compounding and time value --------------------------------------
    {
        'question': 'Invest ₹5,000 a month for 20 years at 12%. What does it grow to?',
        'answer': 4997000,
        'unit': '₹',
        'context': 'You contribute ₹12 lakh. The other ₹38 lakh is compounding doing the work.',
    },
    {
        'question': 'How much must you invest today at 10% to have ₹1 crore in 25 years?',
        'answer': 923000,
        'unit': '₹',
        'context': 'Under ten lakh, once. Starting early is worth more than investing more.',
    },
    {
        'question': 'By the rule of 72, how many years does money take to double at 9%?',
        'answer': 8,
        'unit': 'years',
        'context': '72 divided by the rate. A shortcut accurate enough for any mental check.',
    },
    {
        'question': 'Invest ₹10,000 a month for 30 years at 12%. What does it become?',
        'answer': 35299000,
        'unit': '₹',
        'context': 'Around ₹3.5 crore from ₹36 lakh of contributions. The last decade adds the most.',
    },
    {
        'question': 'Starting a ₹10,000 SIP at 25 instead of 35, at 12%, how much more do you have at 60?',
        'answer': 31000000,
        'unit': '₹',
        'context': 'Roughly ₹3.1 crore more for ₹12 lakh of extra contributions. Ten years is the whole game.',
    },
    {
        'question': 'What is ₹1 lakh from 2000 worth in today’s money at 6% inflation?',
        'answer': 19000,
        'unit': '₹',
        'context': 'Cash under a mattress lost about four fifths of its value over 25 years.',
    },
    {
        'question': 'At 7% inflation, what monthly income in 30 years matches ₹50,000 today?',
        'answer': 380000,
        'unit': '₹',
        'context': 'Retirement planning fails when people target today’s expenses instead of tomorrow’s.',
    },
    {
        'question': 'How many years to turn ₹1 lakh into ₹1 crore at 15%?',
        'answer': 33,
        'unit': 'years',
        'context': 'A hundredfold at a very good rate still takes a working lifetime.',
    },

    # ----- Loans and EMIs ---------------------------------------------------
    {
        'question': 'On a ₹30 lakh home loan over 20 years at 8.5%, what is the monthly EMI?',
        'answer': 26035,
        'unit': '₹',
        'context': 'Over 20 years you repay about ₹62 lakh — more than double what you borrowed.',
    },
    {
        'question': 'On that same ₹30 lakh loan, how much is interest alone?',
        'answer': 3248000,
        'unit': '₹',
        'context': 'The interest exceeds the principal. Term length costs more than rate shopping saves.',
    },
    {
        'question': 'Cutting a 20-year ₹30 lakh home loan to 15 years, how much interest do you save?',
        'answer': 1050000,
        'unit': '₹',
        'context': 'About ten lakh, for roughly ₹4,000 more a month. The cheapest return available to most people.',
    },
    {
        'question': 'On a ₹8 lakh car loan over 5 years at 9.5%, what is the EMI?',
        'answer': 16800,
        'unit': '₹',
        'context': 'A depreciating asset bought with borrowed money loses twice.',
    },
    {
        'question': 'Paying only the minimum on ₹1 lakh of credit card debt, how many years to clear it?',
        'answer': 20,
        'unit': 'years',
        'context': 'The minimum is designed to keep the balance alive, not to retire it.',
    },
    {
        'question': 'What share of your take-home pay should all EMIs together stay under?',
        'answer': 40,
        'unit': '%',
        'context': 'Lenders will approve more. Above 40% a single missed month becomes a spiral.',
    },

    # ----- Tax --------------------------------------------------------------
    {
        'question': 'What is the maximum deduction under Section 80C per year?',
        'answer': 150000,
        'unit': '₹',
        'context': 'Covers EPF, PPF, ELSS, life premiums and principal on a home loan, combined.',
    },
    {
        'question': 'What is the long-term capital gains tax rate on Indian equity?',
        'answer': 12.5,
        'unit': '%',
        'context': 'On gains above the annual exemption, for holdings over one year.',
    },
    {
        'question': 'What is the annual LTCG exemption on Indian equity gains?',
        'answer': 125000,
        'unit': '₹',
        'context': 'Harvesting up to this much each year resets your cost basis for free.',
    },
    {
        'question': 'What is the short-term capital gains rate on Indian equity?',
        'answer': 20.0,
        'unit': '%',
        'context': 'Selling inside a year costs materially more. Impatience is taxed.',
    },
    {
        'question': 'Up to what income is there no tax under the new regime?',
        'answer': 1200000,
        'unit': '₹',
        'context': 'After the rebate. Above it, slabs apply on the whole amount.',
    },
    {
        'question': 'What is the flat tax rate on gains from crypto in India?',
        'answer': 30,
        'unit': '%',
        'context': 'With no deduction for losses against other income, and 1% TDS on each transfer.',
    },
    {
        'question': 'What deduction can you claim on home loan interest for a self-occupied house?',
        'answer': 200000,
        'unit': '₹',
        'context': 'Under Section 24(b), in the old regime only.',
    },

    # ----- Prices and everyday magnitudes -----------------------------------
    {
        'question': 'Roughly what does 10 grams of 24k gold cost in India?',
        'answer': 118000,
        'unit': '₹',
        'context': 'Gold is the default savings instrument for most Indian households.',
    },
    {
        'question': 'Roughly how many rupees to the US dollar right now?',
        'answer': 88,
        'unit': '₹',
        'context': 'The rupee has lost roughly half its dollar value in twenty years.',
    },
    {
        'question': 'What is the monthly minimum wage for unskilled work in Delhi?',
        'answer': 18066,
        'unit': '₹',
        'context': 'A useful floor for judging whether any income figure is plausible.',
    },
    {
        'question': 'What is India’s per-capita GDP in rupees per year?',
        'answer': 235000,
        'unit': '₹',
        'context': 'Most financial advice written abroad assumes ten times this.',
    },
    {
        'question': 'What is the average annual premium for ₹1 crore of term life cover at age 30?',
        'answer': 12000,
        'unit': '₹',
        'context': 'About a thousand a month. The cheapest financial product most people never buy.',
    },
    {
        'question': 'What does a ₹10 lakh family health cover typically cost per year at 35?',
        'answer': 22000,
        'unit': '₹',
        'context': 'One hospital stay costs more than a decade of premiums.',
    },

    # ----- Markets and funds -------------------------------------------------
    {
        'question': 'What expense ratio does a typical Indian index fund charge?',
        'answer': 0.2,
        'unit': '%',
        'context': 'An active fund charges five to ten times this for returns that usually trail.',
    },
    {
        'question': 'What expense ratio does a typical active Indian equity fund charge?',
        'answer': 1.8,
        'unit': '%',
        'context': 'On ₹10 lakh that is ₹18,000 a year, charged whether the fund wins or loses.',
    },
    {
        'question': 'Over 20 years, how much of a ₹50 lakh corpus does a 2% fee consume?',
        'answer': 33,
        'unit': '%',
        'context': 'A third. Fees compound against you exactly as returns compound for you.',
    },
    {
        'question': 'What share of active Indian large-cap funds beat the index over ten years?',
        'answer': 20,
        'unit': '%',
        'context': 'And you cannot know in advance which fifth it will be.',
    },
    {
        'question': 'How many companies are in the Nifty 50?',
        'answer': 50,
        'unit': 'companies',
        'context': 'Fifty listings carry most of India’s market capitalisation.',
    },
    {
        'question': 'How far did the Nifty 50 fall at the worst of the 2020 crash?',
        'answer': 38,
        'unit': '%',
        'context': 'It recovered within a year. The people who sold at the bottom did not.',
    },
    {
        'question': 'How far did the Sensex fall peak to trough in the 2008 crisis?',
        'answer': 61,
        'unit': '%',
        'context': 'Recovery took roughly five years. This is what equity risk actually looks like.',
    },
    {
        'question': 'What is the minimum lot size in rupees for most Nifty options contracts?',
        'answer': 190000,
        'unit': '₹',
        'context': 'Derivatives are not a beginner product, and the lot size is the first reason.',
    },
    {
        'question': 'What share of Indian retail derivatives traders lose money?',
        'answer': 91,
        'unit': '%',
        'context': 'SEBI’s own study. The average loser lost about ₹1.2 lakh over three years.',
    },
    {
        'question': 'What percentage of Indian households hold any equity investment?',
        'answer': 5.0,
        'unit': '%',
        'context': 'Most household wealth sits in property and gold rather than in listed businesses.',
    },
    {
        'question': 'How many demat accounts exist in India?',
        'answer': 190000000,
        'unit': 'accounts',
        'context': 'Roughly 19 crore, up from about 4 crore in 2020.',
    },

    # ----- Behaviour and planning -------------------------------------------
    {
        'question': 'How many months of expenses belongs in an emergency fund?',
        'answer': 6,
        'unit': 'months',
        'context': 'Six months of costs, not income, and held somewhere you can reach the same day.',
    },
    {
        'question': 'What multiple of annual income should your life cover be, at minimum?',
        'answer': 10,
        'unit': 'x',
        'context': 'Ten times income, plus outstanding loans, minus what you have already saved.',
    },
    {
        'question': 'What multiple of final annual expenses do you need to retire at a 4% withdrawal rate?',
        'answer': 25,
        'unit': 'x',
        'context': 'Twenty-five times. It is the same arithmetic as 4%, read the other way round.',
    },
    {
        'question': 'What share of income does the 50/30/20 rule assign to savings?',
        'answer': 20,
        'unit': '%',
        'context': 'Needs 50, wants 30, future 20. The last one is the one people cut first.',
    },
    {
        'question': 'How much does the average equity fund investor underperform their own fund by, annually?',
        'answer': 1.7,
        'unit': '%',
        'context': 'The gap is entirely buying high and selling low. Doing nothing beats most people.',
    },
    {
        'question': 'Missing the ten best market days over twenty years cuts your return by how much?',
        'answer': 50,
        'unit': '%',
        'context': 'Roughly half. The best days cluster next to the worst ones, which is why timing fails.',
    },
    {
        'question': 'What is the maximum annual contribution to a PPF account?',
        'answer': 150000,
        'unit': '₹',
        'context': 'Per person per year, across all PPF accounts they hold.',
    },
    {
        'question': 'How long is the lock-in on an ELSS mutual fund?',
        'answer': 3,
        'unit': 'years',
        'context': 'The shortest lock-in of any 80C option, and the only one holding equity.',
    },
    {
        'question': 'How much deposit insurance does DICGC cover per bank per depositor?',
        'answer': 500000,
        'unit': '₹',
        'context': 'Five lakh. Balances above it in one bank are an unsecured loan to that bank.',
    },
    {
        'question': 'At what age can you start withdrawing from the NPS without penalty?',
        'answer': 60,
        'unit': 'years',
        'context': 'And 40% of the corpus must buy an annuity at that point.',
    },
)
