"""
The scenario bank.

Each entry is one financial decision with three defensible-looking options, only
one of which is actually best. The wrong answers are the ones people really
choose — take the EMI, trust the relative, chase the tip — because a scenario
whose bad options are obviously bad teaches nothing.

Every option carries the arithmetic as well as the verdict: what it does to the
balance now (``impact``), what the money does afterwards (``growth``), and how
it moves confidence and risk. ``score`` is what the player earns, 0 to 20.

Loaded by ``manage.py seed_scenarios``, keyed on title, so re-running updates in
place rather than duplicating.
"""

from typing import NamedTuple


class Choice(NamedTuple):
    """One option in a scenario."""

    text: str
    kind: str  # INVEST, SAVE or SPEND
    score: int  # 0-20
    impact: int  # immediate change to the balance, in rupees
    growth: float  # annual growth the committed money then earns
    confidence: int
    risk: int
    why: str  # what actually happens, and why
    mentor: str  # one line the mentor says back


class Case(NamedTuple):
    """One scenario and its options."""

    title: str
    description: str
    balance: int
    options: tuple[Choice, ...]


# --------------------------------------------------------------------------- #
# Income and windfalls                                                         #
# --------------------------------------------------------------------------- #

INCOME = (
    Case(
        'The First Salary',
        'Your first paycheck of ₹50,000 just landed. Everyone has an opinion about '
        'what you should do with it. What actually happens to the money?',
        50_000,
        (
            Choice(
                'Start a ₹10,000 monthly SIP', 'INVEST', 20, -10_000, 0.12, 10, 10,
                'A ₹10,000 SIP started at 22 instead of 32 is worth roughly ₹3 crore more by 60. '
                'The decade you start in matters more than the amount.',
                'The best thing about this decision is its date.',
            ),
            Choice(
                'Park it in the savings account', 'SAVE', 8, -10_000, 0.03, 5, -5,
                'Safe in nominal terms and a slow loss in real ones: 3% against 6% inflation '
                'means the money buys less every year it sits there.',
                'Not wrong, just standing still.',
            ),
            Choice(
                'Celebrate properly — you earned it', 'SPEND', 3, -20_000, 0.0, -5, 20,
                'Forty percent of a first salary on one night sets the reference point for '
                'every month after it. Celebrate, but at 5% not 40%.',
                'Mark the moment. Do not anchor your lifestyle to it.',
            ),
        ),
    ),
    Case(
        'Diwali Bonus',
        'A ₹1,00,000 Diwali bonus arrives. It is not in any budget you have written, '
        'which is exactly what makes it dangerous.',
        100_000,
        (
            Choice(
                'Clear the ₹80,000 credit card balance', 'SAVE', 20, -80_000, 0.42, 15, -25,
                'Clearing 42% debt is a guaranteed 42% return. No investment available to you '
                'pays that, and none of them are certain.',
                'Paying off card debt is the highest guaranteed return you will ever get.',
            ),
            Choice(
                'Put the whole bonus into equity', 'INVEST', 10, -100_000, 0.12, 5, 20,
                'Investing at 12% while carrying 42% debt loses 30% a year. The maths is not close.',
                'Good instinct, wrong order. Debt first.',
            ),
            Choice(
                'Upgrade the phone and keep the rest', 'SPEND', 3, -60_000, 0.0, -5, 15,
                'The phone loses half its value in two years while the card balance compounds monthly.',
                'Two depreciating assets at once.',
            ),
        ),
    ),
    Case(
        'The Raise',
        'A 20% raise takes your take-home from ₹60,000 to ₹72,000. Nobody is watching '
        'what you do with the extra ₹12,000.',
        72_000,
        (
            Choice(
                'Raise the SIP by the full ₹12,000', 'INVEST', 20, -12_000, 0.12, 12, 8,
                'You never adjusted to the money, so you will not miss it. This is the single '
                'most effective habit in personal finance.',
                'Invest the raise before your lifestyle notices it arrived.',
            ),
            Choice(
                'Split it: half saved, half enjoyed', 'INVEST', 15, -6_000, 0.12, 8, 5,
                'A sustainable compromise. Half a raise invested still compounds, and a plan '
                'you actually keep beats a stricter one you abandon.',
                'Sustainable beats optimal.',
            ),
            Choice(
                'Move to a nicer flat', 'SPEND', 2, -12_000, 0.0, -5, 20,
                'Lifestyle inflation is permanent in a way the raise is not. Rent is the hardest '
                'expense to reverse once you have signed.',
                'The raise disappeared before it cleared.',
            ),
        ),
    ),
    Case(
        'Freelance Windfall',
        'A side project pays ₹2,00,000 in one go. No TDS was deducted and nobody '
        'reminded you about tax.',
        200_000,
        (
            Choice(
                'Set aside 30% for tax, invest the rest', 'SAVE', 20, -60_000, 0.07, 12, -10,
                'Freelance income is taxed at your slab with no employer deducting it. People '
                'who spend the gross amount meet the bill in July with nothing left.',
                'The taxman is a silent partner in every freelance rupee.',
            ),
            Choice(
                'Invest all of it immediately', 'INVEST', 8, -200_000, 0.12, 5, 20,
                'You will be selling investments at a loss in July to pay a bill you already knew about.',
                'Enthusiasm, meet advance tax.',
            ),
            Choice(
                'Treat it as free money', 'SPEND', 0, -150_000, 0.0, -10, 30,
                'It was never free. It was gross income with a tax liability already attached.',
                'Nothing that arrives with a tax bill is a windfall.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Debt                                                                         #
# --------------------------------------------------------------------------- #

DEBT = (
    Case(
        'The Credit Card Trap',
        'Your card statement shows ₹45,000 outstanding. The minimum due is ₹2,250 '
        'and the bank has helpfully highlighted only that number.',
        60_000,
        (
            Choice(
                'Pay the full ₹45,000 today', 'SAVE', 20, -45_000, 0.42, 15, -30,
                'Interest stops the day the balance does. At 3.5% a month, waiting one more '
                'cycle costs ₹1,575 for nothing.',
                'There is no clever way to carry card debt.',
            ),
            Choice(
                'Convert it to a 12-month EMI at 14%', 'SAVE', 14, -4_000, 0.14, 5, -10,
                'Better than revolving at 42%, worse than clearing it. Worth doing only if you '
                'genuinely cannot pay in full.',
                'A real improvement, and still an admission.',
            ),
            Choice(
                'Pay the minimum and deal with it later', 'SPEND', 0, -2_250, 0.42, -15, 35,
                'The minimum is engineered to keep the balance alive. At this rate the ₹45,000 '
                'takes over fifteen years and costs more than double.',
                'The minimum due is the bank’s business model, not your plan.',
            ),
        ),
    ),
    Case(
        'Loan for the Wedding',
        'The family wedding budget has reached ₹15,00,000. A bank will lend it at '
        '13% over five years, and everyone is treating that as settled.',
        500_000,
        (
            Choice(
                'Cut the guest list and pay from savings', 'SAVE', 20, -500_000, 0.0, 10, -20,
                'A ₹15 lakh loan costs ₹34,000 a month for five years — ₹5.5 lakh of it interest. '
                'Starting a marriage owing that is a choice, not an obligation.',
                'The wedding lasts a day. The EMI lasts sixty months.',
            ),
            Choice(
                'Borrow half, fund the rest yourself', 'SAVE', 12, -500_000, 0.13, 0, 15,
                'Halves the damage. Still ₹17,000 a month that could have been a SIP.',
                'Less bad. Still a bill for one evening.',
            ),
            Choice(
                'Take the full loan — it is once in a lifetime', 'SPEND', 2, 0, 0.13, -5, 35,
                'Five years of EMIs on an event that is over in eight hours, during the exact '
                'years compounding would have done the most.',
                'Borrowing for a party is borrowing against your thirties.',
            ),
        ),
    ),
    Case(
        'Buying a Car',
        'You want a ₹9,00,000 car. The showroom offers 100% finance at 9.5% and '
        'frames the EMI as "less than you spend on coffee".',
        400_000,
        (
            Choice(
                'Buy a ₹4,00,000 used car in cash', 'SAVE', 20, -400_000, 0.0, 10, -10,
                'A three-year-old car has already taken its worst depreciation. You get the same '
                'transport with none of the interest.',
                'Let the first owner pay for the depreciation.',
            ),
            Choice(
                'Pay ₹3,00,000 down, finance ₹6,00,000', 'SPEND', 10, -300_000, 0.095, 0, 15,
                'A real compromise, but you are still paying interest on something losing value.',
                'Borrowing against a depreciating asset always costs twice.',
            ),
            Choice(
                'Take the full finance and keep the cash', 'SPEND', 3, 0, 0.095, -5, 25,
                '₹9 lakh at 9.5% over five years costs ₹2.3 lakh in interest on an asset worth '
                'half by the end.',
                'The car loses value while the loan does not.',
            ),
        ),
    ),
    Case(
        'Education Loan Decision',
        'A master’s costs ₹20,00,000. You have ₹8,00,000 saved. The loan is at 9%, '
        'and the degree plausibly doubles your salary.',
        800_000,
        (
            Choice(
                'Pay ₹8,00,000 down and borrow ₹12,00,000', 'INVEST', 20, -800_000, 0.09, 12, 10,
                'Education is the rare borrowing where the asset appreciates. Minimising the '
                'principal while keeping a cash buffer is the balance.',
                'Borrow for things that earn. This qualifies.',
            ),
            Choice(
                'Borrow the whole amount, invest your savings', 'INVEST', 12, 0, 0.09, 5, 20,
                'Paying 9% to earn a hoped-for 12% is a leveraged bet with your tuition.',
                'Arbitrage on your own education is thinner than it looks.',
            ),
            Choice(
                'Skip the degree and keep the cash', 'SAVE', 6, 0, 0.06, -5, 0,
                'Sometimes right, but here the numbers favour going. A doubled salary repays '
                '₹12 lakh quickly.',
                'Avoiding all debt is its own kind of expensive.',
            ),
        ),
    ),
    Case(
        'The Prepayment Question',
        'You have ₹5,00,000 spare and a home loan at 8.5% with fifteen years left. '
        'Equity has returned about 12% historically.',
        500_000,
        (
            Choice(
                'Prepay the loan', 'SAVE', 16, -500_000, 0.085, 10, -20,
                'A guaranteed 8.5% after tax, and fifteen years of certainty. For most people '
                'the certainty is worth more than the spread.',
                'A guaranteed 8.5% beats a hoped-for 12%.',
            ),
            Choice(
                'Invest it in equity instead', 'INVEST', 14, -500_000, 0.12, 5, 15,
                'Defensible if your horizon is long and your nerve holds. The gap is real but '
                'it is not free — it is paid for in volatility.',
                'A reasonable bet, not a free lunch.',
            ),
            Choice(
                'Split it evenly', 'INVEST', 18, -500_000, 0.10, 12, -5,
                'Captures most of the spread and most of the certainty, and you will not regret '
                'either half whichever way markets go.',
                'When two answers are both defensible, take both.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Protection                                                                   #
# --------------------------------------------------------------------------- #

PROTECTION = (
    Case(
        'The Insurance Sales Pitch',
        'An agent offers a policy: ₹50,000 a year, life cover of ₹5,00,000, and '
        '"guaranteed returns". He mentions Section 80C four times.',
        50_000,
        (
            Choice(
                'Buy term cover and invest the difference', 'INVEST', 20, -50_000, 0.12, 15, -10,
                '₹1 crore of term cover costs about ₹12,000 a year. The other ₹38,000 invested '
                'does far more than a policy returning 4-5%.',
                'Insurance is for protection. Investment is for returns. Never one product.',
            ),
            Choice(
                'Buy the endowment policy', 'SAVE', 4, -50_000, 0.045, -5, 10,
                'Twenty times less cover, returns below inflation, and a lock-in that makes '
                'leaving expensive. The commission is why it was offered.',
                'Sold, not bought.',
            ),
            Choice(
                'Skip insurance entirely and invest it all', 'INVEST', 8, -50_000, 0.12, 0, 30,
                'Right about the product, wrong about the need. If anyone depends on your '
                'income, uninsured is a bet you cannot cover.',
                'Correct diagnosis, dangerous prescription.',
            ),
        ),
    ),
    Case(
        'Health Cover Gap',
        'Your employer covers you for ₹3,00,000. A relative’s ICU stay just cost '
        '₹8,00,000, and your cover ends the day your job does.',
        40_000,
        (
            Choice(
                'Buy ₹10,00,000 of personal cover', 'SAVE', 20, -22_000, 0.0, 15, -30,
                'About ₹22,000 a year at 35. Employer cover vanishes with the job and does not '
                'follow you into the illness that caused you to leave.',
                'The cover you own is the only cover you can count on.',
            ),
            Choice(
                'Top up the employer policy', 'SAVE', 12, -9_000, 0.0, 8, -15,
                'Cheaper and better than nothing, but still tied to the employer underneath it.',
                'Half a solution to a whole problem.',
            ),
            Choice(
                'Rely on the employer policy', 'SPEND', 2, 0, 0.0, -10, 35,
                'One hospital stay above ₹3 lakh wipes out years of saving, and job loss and '
                'illness arrive together more often than people expect.',
                'A policy your employer can cancel is not your policy.',
            ),
        ),
    ),
    Case(
        'The Emergency Fund Question',
        'You have ₹3,00,000 saved and monthly expenses of ₹50,000. A colleague says '
        'holding cash is "losing to inflation".',
        300_000,
        (
            Choice(
                'Keep six months liquid, invest the rest', 'SAVE', 20, -300_000, 0.08, 15, -25,
                '₹3 lakh is exactly six months. Keeping it accessible is what stops the next '
                'emergency becoming credit card debt at 42%.',
                'The emergency fund is not an investment. It is what stops you borrowing.',
            ),
            Choice(
                'Invest most of it, keep one month', 'INVEST', 8, -250_000, 0.12, 0, 25,
                'Emergencies do not check whether the market is down before arriving.',
                'You have optimised the return and removed the point.',
            ),
            Choice(
                'Keep all of it in the savings account', 'SAVE', 10, 0, 0.03, 5, -10,
                'Safe and slightly wasteful. Six months liquid is prudent; twelve is idle.',
                'Cautious past the point where caution helps.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Markets and behaviour                                                        #
# --------------------------------------------------------------------------- #

MARKETS = (
    Case(
        'Market Crash',
        'The index is down 30% in three weeks. Your ₹10,00,000 portfolio is worth '
        '₹7,00,000 and every headline says it will get worse.',
        700_000,
        (
            Choice(
                'Keep the SIP running and add if you can', 'INVEST', 20, -50_000, 0.14, 15, 10,
                'Every unit bought in a crash is bought cheap. The 2020 crash recovered in a '
                'year; the people who sold at the bottom did not recover with it.',
                'The discount is real. Your horizon has not changed.',
            ),
            Choice(
                'Pause the SIP and wait for clarity', 'SAVE', 6, 0, 0.03, -5, 10,
                'Clarity arrives after the recovery, which is how people reliably miss it.',
                'Waiting for certainty means buying at the top.',
            ),
            Choice(
                'Sell and move to safety', 'SPEND', 0, 0, 0.03, -20, 25,
                'This converts a paper loss into a real one and guarantees you miss the rebound. '
                'Missing the ten best days over twenty years halves your return.',
                'You have sold the recovery along with the crash.',
            ),
        ),
    ),
    Case(
        'The Crypto Tip',
        'A friend has tripled their money in a coin you have never heard of and '
        'wants you in before "it goes parabolic".',
        100_000,
        (
            Choice(
                'Stay out entirely', 'SAVE', 18, 0, 0.08, 10, -15,
                'You cannot value it, which means you cannot tell a dip from a collapse. That '
                'is not investing, and gains are taxed at 30% with losses not offsettable.',
                'If you cannot say what it is worth, you are not investing.',
            ),
            Choice(
                'Put in 2% you can afford to lose', 'INVEST', 14, -2_000, 0.20, 5, 20,
                'A position small enough that a total loss changes nothing is a legitimate way '
                'to learn. Size is what makes it survivable.',
                'A position you can lose entirely is a position you can think clearly about.',
            ),
            Choice(
                'Put in ₹50,000 before it runs', 'INVEST', 0, -50_000, 0.20, -15, 40,
                'Half your liquid savings on a tip, after the move has already happened. The '
                'person telling you needs someone to sell to.',
                'You are the exit liquidity.',
            ),
        ),
    ),
    Case(
        'The IPO Hype',
        'An IPO is 80 times subscribed. Every channel is running it. The grey market '
        'premium suggests a 40% listing pop.',
        150_000,
        (
            Choice(
                'Skip it and stay with your plan', 'SAVE', 18, 0, 0.11, 10, -10,
                'Retail gets a sliver of an 80x subscription, and most IPOs trade below their '
                'listing price within a year. The excitement is the product.',
                'Nobody sells you a bargain on television.',
            ),
            Choice(
                'Apply for one lot only', 'INVEST', 14, -15_000, 0.12, 5, 15,
                'A capped bet on a lottery. Fine as long as you know that is what it is.',
                'Treat it as a ticket, not a thesis.',
            ),
            Choice(
                'Apply through three family accounts', 'INVEST', 2, -45_000, 0.12, -10, 35,
                'Tripling the size of a bet you admit is a lottery, in a company you have not '
                'read a page about.',
                'Conviction should come from the accounts, not the account count.',
            ),
        ),
    ),
    Case(
        'The Hot Fund',
        'A fund returned 45% last year and is everywhere. Yours returned 12%. '
        'Switching takes two clicks.',
        500_000,
        (
            Choice(
                'Stay put and keep contributing', 'INVEST', 20, -10_000, 0.12, 12, 0,
                'Last year’s winner is rarely next year’s. Chasing performance is most of the '
                '1.7% a year by which the average investor trails their own funds.',
                'You are buying a past you cannot own.',
            ),
            Choice(
                'Move a quarter of the portfolio', 'INVEST', 10, -125_000, 0.12, 0, 15,
                'Smaller version of the same mistake, plus exit load and a capital gains bill.',
                'A quarter of a bad idea is still the idea.',
            ),
            Choice(
                'Switch everything to the winner', 'INVEST', 2, -500_000, 0.12, -10, 30,
                'Selling a year of gains triggers tax, and 45% years are usually followed by '
                'reversion rather than repetition.',
                'Buying high, with a tax bill for the privilege.',
            ),
        ),
    ),
    Case(
        'Timing the Entry',
        'You have ₹6,00,000 to invest. The market is at an all-time high and every '
        'second person says a correction is due.',
        600_000,
        (
            Choice(
                'Stagger it over six months', 'INVEST', 20, -600_000, 0.12, 12, 0,
                'Captures most of the long-run return while removing the single worst outcome: '
                'the whole sum invested on exactly the wrong day.',
                'Spreading the entry buys you the ability to sleep.',
            ),
            Choice(
                'Invest all of it now', 'INVEST', 14, -600_000, 0.12, 5, 20,
                'Statistically better on average — markets rise more often than they fall — but '
                'the worst case is the one people abandon their plan over.',
                'Right on the maths, hard on the nerves.',
            ),
            Choice(
                'Wait in cash for the correction', 'SAVE', 4, 0, 0.03, -10, 10,
                '"All-time high" describes most of market history. Waiting has cost more than '
                'corrections have.',
                'The correction you are waiting for may start from higher than today.',
            ),
        ),
    ),
    Case(
        'Loss Aversion',
        'One holding is down 40%. Another is up 60%. You need ₹1,00,000 for '
        'something and must sell one of them.',
        100_000,
        (
            Choice(
                'Sell whichever you would not buy today', 'INVEST', 20, -100_000, 0.12, 15, -10,
                'The only question that matters is which you would buy now at today’s price. '
                'What you paid is gone and is not information.',
                'The purchase price is the one number the market ignores.',
            ),
            Choice(
                'Sell the winner and keep the loser', 'INVEST', 6, -100_000, 0.08, -5, 20,
                'The disposition effect: selling winners to feel right and holding losers to '
                'avoid feeling wrong. It reliably costs money.',
                'You have sold the evidence and kept the mistake.',
            ),
            Choice(
                'Sell the loser to book the loss', 'INVEST', 14, -100_000, 0.10, 8, 0,
                'Defensible — the realised loss offsets gains at tax time — as long as it is the '
                'one you would not buy today.',
                'Tax-loss harvesting is real, but it is not a reason on its own.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Fraud and pressure                                                           #
# --------------------------------------------------------------------------- #

FRAUD = (
    Case(
        'The Guaranteed Return',
        'A scheme promises 3% a month — 36% a year — "fully guaranteed", with '
        'testimonials and an office you can visit.',
        200_000,
        (
            Choice(
                'Refuse and report it', 'SAVE', 20, 0, 0.08, 15, -20,
                'Guaranteed and 36% cannot both be true. Government debt pays 7%; anything '
                'promising five times that with certainty is paying old investors with new money.',
                'Guaranteed and high are the two words that never appear together honestly.',
            ),
            Choice(
                'Test it with a small amount', 'INVEST', 4, -20_000, 0.0, -5, 35,
                'The early payouts are the hook. They are funded by your own principal and the '
                'next entrant’s.',
                'The test is designed to pass.',
            ),
            Choice(
                'Invest after seeing a friend get paid', 'INVEST', 0, -200_000, 0.0, -20, 45,
                'Every Ponzi pays early investors. That is the mechanism, not the evidence.',
                'The friend getting paid is the advertisement.',
            ),
        ),
    ),
    Case(
        'The Urgent Call',
        'Someone from "your bank" says your account is compromised and reads out '
        'your last transaction correctly. They need an OTP to secure it.',
        80_000,
        (
            Choice(
                'Hang up and call the number on your card', 'SAVE', 20, 0, 0.06, 15, -25,
                'No bank ever asks for an OTP. Knowing a recent transaction proves a data leak, '
                'not that they work there.',
                'Hang up. Call back on a number you found yourself.',
            ),
            Choice(
                'Ask questions but stay on the line', 'SAVE', 8, 0, 0.06, 0, 15,
                'Staying on gives a trained caller more time to work. Urgency is the tool.',
                'Every extra second is on their side.',
            ),
            Choice(
                'Share the OTP to secure the account', 'SPEND', 0, -80_000, 0.0, -25, 50,
                'The OTP authorises the transfer out. The call was the attack, not the warning.',
                'The OTP is the transfer. There is nothing to secure.',
            ),
        ),
    ),
    Case(
        'Lending to a Friend',
        'A close friend asks for ₹2,00,000 for a "sure thing" business and promises '
        'to repay in six months.',
        300_000,
        (
            Choice(
                'Give what you can afford to lose, as a gift', 'SPEND', 18, -50_000, 0.0, 10, 5,
                'Deciding in advance that it will not come back is the only version that leaves '
                'the friendship intact either way.',
                'Lend what you can afford to give away.',
            ),
            Choice(
                'Lend it with written terms', 'SAVE', 12, -200_000, 0.0, 0, 20,
                'Better than a handshake, and you will still be the one chasing it in month nine.',
                'The paperwork protects the money, not the friendship.',
            ),
            Choice(
                'Lend it on trust — they are family', 'SPEND', 4, -200_000, 0.0, -10, 35,
                'Most informal loans between friends are never fully repaid, and the relationship '
                'usually goes with the money.',
                'You are risking two things, and only one of them is rupees.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Housing, tax and the long horizon                                            #
# --------------------------------------------------------------------------- #

LONG_TERM = (
    Case(
        'Rent versus Buy',
        'Rent on your flat is ₹25,000. Buying the same one means a ₹55,000 EMI for '
        'twenty years, and everyone says rent is money down the drain.',
        1_000_000,
        (
            Choice(
                'Keep renting and invest the difference', 'INVEST', 18, -30_000, 0.12, 12, -5,
                '₹30,000 a month invested for twenty years at 12% is about ₹3 crore. Rent buys '
                'flexibility; the difference buys the asset.',
                '"Rent is wasted" ignores what the difference does.',
            ),
            Choice(
                'Buy if you will stay more than seven years', 'SAVE', 18, -1_000_000, 0.08, 10, 10,
                'Stamp duty, registration and brokerage take 8-10% up front. Below seven years '
                'the transaction costs usually swamp the appreciation.',
                'The right answer depends on how long you will stay, not on the rent.',
            ),
            Choice(
                'Buy now before prices rise further', 'SPEND', 4, -1_000_000, 0.08, -5, 30,
                'Buying on urgency rather than horizon, with a ₹55,000 EMI that removes every '
                'other option for twenty years.',
                'Fear of missing out is not a housing strategy.',
            ),
        ),
    ),
    Case(
        'Tax Season Rush',
        'It is March. You need ₹1,50,000 of 80C investment and your inbox is full of '
        'agents offering to solve it today.',
        150_000,
        (
            Choice(
                'Put it in ELSS as a planned SIP next year', 'INVEST', 20, -150_000, 0.12, 15, 5,
                'ELSS has the shortest lock-in at three years and is the only 80C option holding '
                'equity. Spread monthly, it stops being a March panic.',
                'The March rush is a planning failure, not a tax problem.',
            ),
            Choice(
                'Put it in PPF', 'SAVE', 14, -150_000, 0.071, 8, -15,
                'Tax-free and government-backed at 7.1%, locked for fifteen years. Right for the '
                'debt part of a portfolio, slow for the whole of it.',
                'Safe, and a very long time.',
            ),
            Choice(
                'Buy whatever the agent recommends', 'SAVE', 2, -150_000, 0.045, -10, 20,
                'March-sold insurance policies are the most expensive way to save ₹46,800 of tax.',
                'You saved tax and bought a worse product to do it.',
            ),
        ),
    ),
    Case(
        'Early Retirement Maths',
        'You spend ₹60,000 a month and want to stop working at 45. Someone tells you '
        '₹1 crore is plenty.',
        1_000_000,
        (
            Choice(
                'Target 25 times annual expenses', 'INVEST', 20, -100_000, 0.12, 15, 0,
                '₹7.2 lakh a year × 25 is ₹1.8 crore in today’s money, and more by the time you '
                'get there. The 4% rule and the 25x rule are the same arithmetic.',
                'Twenty-five times expenses. Not a number someone told you at a party.',
            ),
            Choice(
                'Aim for ₹1 crore and reassess', 'SAVE', 8, -100_000, 0.10, 0, 20,
                '₹1 crore at 4% yields ₹33,000 a month — a little over half what you spend now, '
                'before thirty years of inflation.',
                'A round number is not a plan.',
            ),
            Choice(
                'Assume the pension will cover it', 'SPEND', 2, 0, 0.06, -10, 30,
                'NPS forces 40% into an annuity at 60, which does not help at 45, and the rest '
                'is whatever you put in.',
                'Retiring at 45 on a plan that starts at 60.',
            ),
        ),
    ),
    Case(
        'The Second Property',
        'A builder offers a ₹60,00,000 flat as an "investment" yielding ₹18,000 a '
        'month in rent, with a ₹52,000 EMI.',
        1_500_000,
        (
            Choice(
                'Decline — the yield does not cover the cost', 'SAVE', 20, 0, 0.11, 12, -15,
                'A 3.6% gross yield against an 8.5% loan is a negative carry of ₹34,000 a month, '
                'before maintenance, vacancy and property tax.',
                'A rental yielding less than the loan is a subscription, not an investment.',
            ),
            Choice(
                'Buy it with a much larger down payment', 'SAVE', 10, -1_500_000, 0.07, 0, 20,
                'Reduces the bleed but concentrates your net worth in one illiquid asset in one '
                'city.',
                'Less leverage, same concentration.',
            ),
            Choice(
                'Buy it — property always goes up', 'SPEND', 2, -1_500_000, 0.07, -10, 35,
                'Indian residential property has underperformed equity over the last decade, '
                'before the costs of holding it.',
                '"Always goes up" is the sentence that precedes every correction.',
            ),
        ),
    ),
    Case(
        'Supporting Parents',
        'Your parents need ₹25,000 a month. You earn ₹90,000 and are three years '
        'into building your own savings.',
        90_000,
        (
            Choice(
                'Budget it as a fixed expense and adjust goals', 'SAVE', 20, -25_000, 0.10, 15, -10,
                'Treating it as a planned commitment rather than a monthly surprise is what keeps '
                'both the support and the saving sustainable.',
                'Plan it in, and your own goals survive it.',
            ),
            Choice(
                'Pause your SIP entirely', 'SAVE', 8, -25_000, 0.03, -5, 15,
                'Understandable and expensive. Even ₹5,000 a month kept running preserves the '
                'habit and a decade of compounding.',
                'Reduce the SIP. Try not to stop it.',
            ),
            Choice(
                'Take a personal loan to cover both', 'SPEND', 0, -25_000, 0.13, -15, 40,
                'Borrowing at 13% to keep investing at 12% loses money with certainty, and the '
                'support is an ongoing need rather than a one-off.',
                'Never borrow to invest. Especially not for a recurring cost.',
            ),
        ),
    ),
    Case(
        'The Job Switch',
        'A new offer pays 40% more but the company is two years old. Your current '
        'job is secure and dull.',
        120_000,
        (
            Choice(
                'Take it, with twelve months of expenses saved first', 'INVEST', 20, -300_000, 0.11, 15, 5,
                'Startup risk is survivable when the runway is personal, not just corporate. The '
                'buffer is what turns a risk into a decision.',
                'Take the risk once you can afford to be wrong about it.',
            ),
            Choice(
                'Take it immediately', 'INVEST', 10, 0, 0.11, 5, 30,
                'The upside is real; so is the chance of a six-month job search with two months '
                'of savings.',
                'Right move, wrong order.',
            ),
            Choice(
                'Stay where it is safe', 'SAVE', 8, 0, 0.08, -5, -10,
                'Security has a price too: a 40% raise compounds across every future salary.',
                'Staying is also a bet, just a quieter one.',
            ),
        ),
    ),
)


BANK: tuple[Case, ...] = INCOME + DEBT + PROTECTION + MARKETS + FRAUD + LONG_TERM


# --------------------------------------------------------------------------- #
# Spending and everyday discipline                                             #
# --------------------------------------------------------------------------- #

HABITS = (
    Case(
        'Subscription Creep',
        'A statement audit turns up eleven active subscriptions totalling ₹4,200 a '
        'month. You recognise four of them.',
        50_000,
        (
            Choice(
                'Cancel everything, re-add only what you miss', 'SAVE', 20, -1_200, 0.12, 12, -15,
                '₹3,000 a month freed and invested at 12% is about ₹30 lakh over twenty-five '
                'years. Cancelling first and re-adding is the only audit that works.',
                'Make each one earn its place back.',
            ),
            Choice(
                'Cancel the obvious ones', 'SAVE', 12, -3_000, 0.12, 6, -8,
                'Real progress. The ones you kept "just in case" are the ones that renew silently.',
                'Better. The survivors are still worth a second look.',
            ),
            Choice(
                'Leave them — it is only a few hundred each', 'SPEND', 2, -4_200, 0.0, -5, 15,
                'Small recurring charges are the hardest spending to notice and the easiest to cut.',
                'The size is why it survives, not why it is fine.',
            ),
        ),
    ),
    Case(
        'The UPI Blur',
        'You cannot say where ₹18,000 went last month. Every payment was two taps '
        'and none of them felt like spending.',
        60_000,
        (
            Choice(
                'Track every rupee for one month', 'SAVE', 20, 0, 0.10, 15, -20,
                'You cannot fix what you cannot see. One month of tracking usually finds 15-20% '
                'of spending nobody would defend out loud.',
                'One month of honesty is worth a year of intentions.',
            ),
            Choice(
                'Set a weekly cash limit instead', 'SAVE', 14, 0, 0.08, 8, -10,
                'Friction works. Cash is felt in a way a tap is not, though it tells you less '
                'about where the money actually goes.',
                'Friction helps. Data helps more.',
            ),
            Choice(
                'Assume it balances out', 'SPEND', 2, -18_000, 0.0, -8, 20,
                '₹18,000 a month unaccounted for is ₹2.1 lakh a year — an entire SIP, invisible.',
                'It does not balance out. It compounds.',
            ),
        ),
    ),
    Case(
        'Buy Now, Pay Later',
        'A ₹40,000 laptop offers "no cost EMI" over twelve months. The checkout page '
        'calls it interest-free.',
        70_000,
        (
            Choice(
                'Pay in full and ask for the cash discount', 'SAVE', 18, -37_000, 0.0, 10, -10,
                'The interest is usually in the price. Asking for the cash price often reveals a '
                '5-8% discount that the EMI quietly absorbed.',
                'No-cost EMI means the cost moved, not that it left.',
            ),
            Choice(
                'Take the EMI and invest the difference', 'INVEST', 14, -3_333, 0.12, 5, 10,
                'Genuinely sound if the EMI really is free and you actually invest the rest. Most '
                'people do the first half.',
                'Works if you do the part nobody does.',
            ),
            Choice(
                'Take the EMI and buy a better model', 'SPEND', 2, -4_500, 0.0, -8, 25,
                'Easy instalments reliably raise what people buy. That is the point of offering them.',
                'The EMI did not save you money. It raised your budget.',
            ),
        ),
    ),
    Case(
        'The Rent Hike',
        'Your landlord wants ₹32,000, up from ₹25,000. Moving costs about ₹40,000 '
        'all in and takes two weekends.',
        150_000,
        (
            Choice(
                'Negotiate, citing nearby listings', 'SAVE', 20, 0, 0.10, 12, -10,
                'A vacant month costs the landlord more than the increase earns. Most hikes are '
                'an opening position, and few tenants test it.',
                'The first number is rarely the last one.',
            ),
            Choice(
                'Move somewhere cheaper', 'SAVE', 12, -40_000, 0.10, 5, 5,
                'Worth it if the saving exceeds ₹40,000 within a year. Below that the move costs '
                'more than the hike.',
                'Do the arithmetic before the packing.',
            ),
            Choice(
                'Accept it to avoid the hassle', 'SPEND', 6, -7_000, 0.0, -5, 10,
                '₹84,000 a year to avoid two weekends, and it becomes the base for the next hike.',
                'Convenience priced per year looks different.',
            ),
        ),
    ),
    Case(
        'Gadget Upgrade Cycle',
        'Your two-year-old phone works. The new one is ₹95,000 and the exchange '
        'offer expires on Sunday.',
        120_000,
        (
            Choice(
                'Keep the phone until it actually fails', 'SAVE', 18, 0, 0.12, 10, -10,
                'Stretching a phone from two years to four halves the lifetime cost. Invested '
                'instead, a skipped upgrade is about ₹3 lakh over twenty years.',
                'A working phone is not a problem that needs solving.',
            ),
            Choice(
                'Upgrade but buy last year’s flagship', 'SPEND', 12, -45_000, 0.0, 5, 5,
                'Most of the capability at half the price, and the depreciation has already happened.',
                'A year of patience is worth about half the price.',
            ),
            Choice(
                'Buy it before the offer ends', 'SPEND', 3, -95_000, 0.0, -5, 20,
                'The deadline is the sales technique. Exchange offers run continuously.',
                'Offers that expire on Sunday reappear on Monday.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Products and paperwork                                                       #
# --------------------------------------------------------------------------- #

PRODUCTS = (
    Case(
        'Direct or Regular',
        'Your advisor recommends the regular plan of a fund. The direct plan of the '
        'same fund charges 0.8% less every year.',
        500_000,
        (
            Choice(
                'Buy the direct plan', 'INVEST', 20, -500_000, 0.12, 15, 0,
                'Same fund, same manager, same portfolio. Over twenty years 0.8% a year on ₹5 '
                'lakh is roughly ₹7 lakh of difference, all of it commission.',
                'Identical fund. One of them pays someone else.',
            ),
            Choice(
                'Stay regular for the advice', 'INVEST', 8, -500_000, 0.112, 0, 10,
                'Worth it only if the advice is real and ongoing. Usually the commission is the '
                'relationship.',
                'Pay for advice if you get advice.',
            ),
            Choice(
                'Split between both to compare', 'INVEST', 6, -500_000, 0.116, -5, 10,
                'There is nothing to compare. The plans are the same portfolio with different fees.',
                'You already know which one wins.',
            ),
        ),
    ),
    Case(
        'The Nominee Nobody Added',
        'You have ₹12,00,000 across four accounts and not one of them has a nominee '
        'recorded. It takes ten minutes to fix.',
        50_000,
        (
            Choice(
                'Add nominees everywhere this week', 'SAVE', 20, 0, 0.10, 15, -25,
                'Without a nominee, a claim needs a succession certificate: months of court time '
                'and legal cost, at the worst possible moment for the people left behind.',
                'Ten minutes now, or a year of court later for someone else.',
            ),
            Choice(
                'Add them to the largest account only', 'SAVE', 10, 0, 0.10, 6, -10,
                'Partial cover. The smaller accounts still need the same certificate.',
                'The paperwork does not scale with the balance.',
            ),
            Choice(
                'Write a will later instead', 'SAVE', 8, 0, 0.10, 0, 10,
                'A will is better and slower. Nominees are ten minutes and work immediately; do '
                'both, in that order.',
                'Do the fast one first.',
            ),
        ),
    ),
    Case(
        'Credit Score Surprise',
        'A home loan application is rejected. Your score is 640, dragged down by a '
        'card you closed and a ₹3,000 bill you forgot in 2023.',
        200_000,
        (
            Choice(
                'Dispute the error and pay down utilisation', 'SAVE', 20, -40_000, 0.08, 15, -20,
                'Utilisation is 30% of the score and errors are common. Six months of paying on '
                'time and staying under 30% usually moves a score 60-80 points.',
                'A score is a habit with a number attached.',
            ),
            Choice(
                'Apply to three other lenders', 'SPEND', 4, 0, 0.09, -5, 25,
                'Every application is a hard enquiry. Three in a month lowers the score further.',
                'Shopping around costs points when you do it this way.',
            ),
            Choice(
                'Wait a year and reapply', 'SAVE', 10, 0, 0.08, 0, 0,
                'Time alone helps a little. Time plus fixing the cause helps a lot more.',
                'Waiting works. Waiting and acting works faster.',
            ),
        ),
    ),
    Case(
        'ESOPs on the Table',
        'Your employer offers options worth ₹15,00,000 on paper, vesting over four '
        'years, in place of a ₹3,00,000 annual raise.',
        300_000,
        (
            Choice(
                'Take the raise', 'SAVE', 18, 0, 0.12, 12, -15,
                'Cash is certain, diversified and yours. Options in a private company may never '
                'be liquid, and you already have your salary riding on the same company.',
                'You are concentrated in this company whether you like it or not.',
            ),
            Choice(
                'Take options only if you can afford the strike', 'INVEST', 14, -100_000, 0.15, 5, 25,
                'Exercising costs money and often triggers tax on paper gains you cannot sell.',
                'Options have a bill attached before they have a buyer.',
            ),
            Choice(
                'Take the options — it could be life-changing', 'INVEST', 6, 0, 0.15, -5, 35,
                'Most startup equity ends up worth nothing. Doubling down on your employer is '
                'the least diversified bet available to you.',
                'Your job is already the bet.',
            ),
        ),
    ),
    Case(
        'FD Laddering',
        'You have ₹6,00,000 for a house deposit needed in three years. One-year FDs '
        'pay 6.8%, three-year FDs pay 7.1%.',
        600_000,
        (
            Choice(
                'Ladder it across one, two and three years', 'SAVE', 20, -600_000, 0.069, 12, -15,
                'A ladder keeps a third liquid every year while capturing most of the longer '
                'rate. Breaking a single long FD costs a penalty.',
                'A ladder buys flexibility for a few basis points.',
            ),
            Choice(
                'Lock it all into the three-year FD', 'SAVE', 14, -600_000, 0.071, 6, -10,
                'Slightly more yield, no access. Fine only if the date really is fixed.',
                'The extra 0.3% costs you every option.',
            ),
            Choice(
                'Put it in equity for three years', 'INVEST', 4, -600_000, 0.12, -5, 35,
                'Three years is inside the window where equity can be down 30% on the day you '
                'need it. Money with a date does not belong in equity.',
                'Money with a deadline does not belong in the market.',
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Family and the long view                                                     #
# --------------------------------------------------------------------------- #

FAMILY = (
    Case(
        'Child Education Fund',
        'Your daughter is two. An engineering degree costs ₹15,00,000 today and '
        'education inflation runs near 10%.',
        200_000,
        (
            Choice(
                'Start a ₹15,000 equity SIP now', 'INVEST', 20, -15_000, 0.12, 15, 10,
                'At 10% inflation the degree costs about ₹60 lakh in sixteen years. Sixteen years '
                'is long enough for equity and short enough that starting late does not work.',
                'Sixteen years is exactly the horizon equity is for.',
            ),
            Choice(
                'Use a child insurance plan', 'SAVE', 6, -15_000, 0.05, -5, 15,
                'Bundles poor insurance with poor returns and locks both. The word "child" in '
                'the name is marketing.',
                'The product is named after your goal, not built for it.',
            ),
            Choice(
                'Start in ten years when you earn more', 'SAVE', 2, 0, 0.07, -10, 25,
                'Six years of compounding instead of sixteen means saving roughly four times as '
                'much per month for the same result.',
                'Later is the most expensive word in this app.',
            ),
        ),
    ),
    Case(
        'Wedding Gold',
        'Family tradition expects ₹5,00,000 of gold jewellery. Making charges run '
        '12% and are never recovered on resale.',
        500_000,
        (
            Choice(
                'Buy less jewellery, hold the rest as gold ETFs', 'INVEST', 18, -500_000, 0.085, 12, -5,
                'ETFs carry no making charge, no storage risk and no purity dispute. Buy the '
                'jewellery you will wear and hold the investment separately.',
                'Jewellery is for wearing. Gold is for holding.',
            ),
            Choice(
                'Buy the full amount in jewellery', 'SAVE', 6, -500_000, 0.07, -5, 10,
                '₹60,000 of making charges vanish the moment you leave the shop.',
                'You paid ₹60,000 for the shape.',
            ),
            Choice(
                'Buy digital gold on an app', 'INVEST', 10, -500_000, 0.08, 0, 20,
                'No making charge, but unregulated custody and a 3% spread. ETFs and sovereign '
                'bonds do the same job under supervision.',
                'Right idea, least protected wrapper.',
            ),
        ),
    ),
    Case(
        'Medical Bill Abroad',
        'A parent needs treatment costing ₹6,00,000. You have ₹3,00,000 liquid and '
        'a ₹12,00,000 equity portfolio that is down 15%.',
        300_000,
        (
            Choice(
                'Use the emergency fund, then a top-up loan', 'SAVE', 18, -300_000, 0.10, 10, 10,
                'This is exactly what the emergency fund exists for. A short secured loan for the '
                'remainder beats selling equity at a 15% loss.',
                'This is the emergency the fund was for.',
            ),
            Choice(
                'Sell equity to cover all of it', 'INVEST', 8, -600_000, 0.0, -5, 20,
                'Crystallises a 15% loss and removes the recovery. Selling into a drawdown is the '
                'single most expensive habit in investing.',
                'The loss is not real until you sell it.',
            ),
            Choice(
                'Put it on credit cards', 'SPEND', 0, -600_000, 0.42, -20, 45,
                '₹6 lakh at 42% adds ₹21,000 a month in interest alone, on top of everything else '
                'happening.',
                'The worst rate available, at the worst possible time.',
            ),
        ),
    ),
    Case(
        'Inflation on the Grocery Bill',
        'The same weekly shop cost ₹2,800 last year and costs ₹3,150 now. Your '
        'salary rose 4%.',
        60_000,
        (
            Choice(
                'Negotiate pay against real inflation', 'SAVE', 18, 0, 0.10, 12, -5,
                'Food inflation at 12.5% against a 4% raise is a real pay cut. Most people '
                'negotiate against last year’s salary rather than against prices.',
                'A 4% raise in a 7% year is a pay cut with good manners.',
            ),
            Choice(
                'Cut the grocery budget', 'SAVE', 10, -350, 0.08, 5, 5,
                'Helps at the margin. Income has far more room to move than a grocery bill does.',
                'You can only cut so far down.',
            ),
            Choice(
                'Absorb it and move on', 'SPEND', 4, -350, 0.0, -5, 15,
                'Absorbed silently every year, this is how real income falls without anyone '
                'noticing a single decision.',
                'Nothing happened, which is the problem.',
            ),
        ),
    ),
    Case(
        'The Side Business Loan',
        'Your small business needs ₹5,00,000 for stock. A bank offers 11% secured '
        'against your flat; an NBFC offers 24% unsecured.',
        200_000,
        (
            Choice(
                'Start smaller with your own ₹2,00,000', 'SAVE', 18, -200_000, 0.18, 12, 5,
                'Proving demand before borrowing is what separates a business from an expensive '
                'hypothesis.',
                'Test the idea before you finance it.',
            ),
            Choice(
                'Take the 11% secured loan', 'INVEST', 12, -500_000, 0.11, 5, 25,
                'Cheaper money, but your home is the collateral. The rate is not the only term.',
                'Read what secures it, not just what it costs.',
            ),
            Choice(
                'Take the 24% unsecured loan', 'SPEND', 2, -500_000, 0.24, -10, 40,
                'The stock must return over 24% just to break even, before you pay yourself '
                'anything.',
                'At 24% the lender is the business.',
            ),
        ),
    ),
    Case(
        'Windfall Inheritance',
        '₹40,00,000 arrives unexpectedly. Six people have already told you what to '
        'do with it, and three of them sell financial products.',
        4_000_000,
        (
            Choice(
                'Park it in liquid funds and decide over three months', 'SAVE', 20, -4_000_000, 0.065, 15, -20,
                'Large sums invite fast decisions and fast decisions are where windfalls go. '
                'Three months in a liquid fund costs almost nothing and prevents almost everything.',
                'The first decision is to not decide yet.',
            ),
            Choice(
                'Invest it all in equity immediately', 'INVEST', 10, -4_000_000, 0.12, 0, 25,
                'Statistically reasonable, psychologically brutal if it drops 20% in month two '
                'and you have never held this much before.',
                'Right on average, hard in practice.',
            ),
            Choice(
                'Buy a flat with it', 'SPEND', 6, -4_000_000, 0.07, -5, 25,
                'Converts a liquid, flexible asset into an illiquid, concentrated one, in a week, '
                'under emotional pressure.',
                'The least reversible option, chosen fastest.',
            ),
        ),
    ),
)


BANK = BANK + HABITS + PRODUCTS + FAMILY
