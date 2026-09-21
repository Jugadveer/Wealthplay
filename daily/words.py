"""
The Ledger word list.

Five letters each, because that is what makes the grid readable at a glance.
Every entry carries the definition shown once the board closes, so a player who
never guesses it still leaves knowing the term — the game is the delivery
mechanism, the definition is the point.

Kept in its own module because a word list is data, not logic, and it will grow.
"""

LEDGER_WORDS: tuple[tuple[str, str], ...] = (
    ('ASSET', 'Anything you own that carries value: cash, a flat, a share.'),
    ('YIELD', 'The income an investment pays, as a percentage of its price.'),
    ('BONDS', 'Loans you make to a government or company, repaid with interest.'),
    ('STOCK', 'A unit of ownership in a company.'),
    ('TRUST', 'A structure that holds assets on someone else’s behalf.'),
    ('VALUE', 'What something is worth, which is not always what it costs.'),
    ('PRICE', 'What the market last paid. Not the same thing as value.'),
    ('TRADE', 'A single buy or sell.'),
    ('MONEY', 'A claim on goods and services that everyone agrees to accept.'),
    ('AUDIT', 'An independent check of a company’s books.'),
    ('BASIS', 'The cost you bought at, used to work out gain or loss.'),
    ('BULLS', 'Investors positioned for prices to rise.'),
    ('BEARS', 'Investors positioned for prices to fall.'),
    ('FLOAT', 'The portion of a company’s shares actually available to trade.'),
    ('FUNDS', 'Pools of money invested together on behalf of many people.'),
    ('GROSS', 'Before deductions. Net is what survives them.'),
    ('HEDGE', 'A position taken to offset the risk of another.'),
    ('INDEX', 'A basket that tracks a whole market, like the Nifty 50.'),
    ('LIMIT', 'An order that fills only at your price or better.'),
    ('QUOTE', 'The current buying and selling price of an asset.'),
    ('RALLY', 'A sustained rise in prices.'),
    ('RATIO', 'One figure divided by another, used to compare companies.'),
    ('SHARE', 'One unit of ownership in a company.'),
    ('SHORT', 'Selling what you do not own, betting the price falls.'),
    ('SPLIT', 'Dividing each share into several cheaper ones.'),
    ('TAXES', 'The government’s cut, which decides your real return.'),
    ('ALPHA', 'Return above what the market itself handed you.'),
    ('DELTA', 'How much an option’s price moves when the asset moves.'),
    ('GAMMA', 'How quickly delta itself changes.'),
    ('THETA', 'The value an option loses each day as expiry approaches.'),
    ('RUPEE', 'India’s currency, and the unit every figure here settles in.'),
    ('LEASE', 'Paying for the use of an asset you do not own.'),
    ('STAKE', 'The size of your holding in something.'),
    ('PRIME', 'The rate banks charge their safest borrowers.'),
    ('DEBIT', 'Money leaving your account.'),
    ('CARRY', 'The cost, or income, of holding a position over time.'),
    ('CHURN', 'Trading often enough that fees eat the return.'),
    ('CYCLE', 'The repeating pattern of expansion and contraction.'),
    ('PANIC', 'Selling on fear rather than on a change in the facts.'),
    ('WAGES', 'Income from work — for most people, the first source of capital.'),
    ('SCRIP', 'A certificate standing in for shares or cash.'),
    ('NAKED', 'An options position with nothing held behind it.'),
    ('ISSUE', 'New shares or bonds sold to raise money.'),
    ('ORDER', 'An instruction to buy or sell.'),
    ('CLOSE', 'The last traded price of the session.'),
)
