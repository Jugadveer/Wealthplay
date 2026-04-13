"""
Nex Mentor Engine - Generates structured educational responses
"""
import json 
import re 
from typing import Dict ,List ,Optional 
from urllib .parse import urlparse ,parse_qs 


class NexMentorEngine :
    """
    Nex - Encouraging, simple, and practical course mentor
    Generates structured responses based on lesson content and sources
    """


    CONCEPT_SOURCES ={
    'investing_basics':[
    {
    "label":"Investopedia - Investing Intro",
    "url":"https://www.investopedia.com/articles/basics/11/3-s-simple-investing.asp"
    },
    {
    "label":"SEBI - Investor Education",
    "url":"https://investor.sebi.gov.in/"
    }
    ],
    'safe_sips':[
    {
    "label":"Groww - SIP Guide",
    "url":"https://groww.in/p/sip-systematic-investment-plan"
    },
    {
    "label":"SEBI - Investor Education",
    "url":"https://investor.sebi.gov.in/"
    }
    ],
    'emergency_fund':[
    {
    "label":"Investopedia - Emergency Fund",
    "url":"https://www.investopedia.com/is-your-emergency-fund-enough-calculate-the-ideal-amount-11723764"
    },
    {
    "label":"SBI Mutual Fund",
    "url":"https://www.sbimf.com/"
    }
    ],
    'diversification':[
    {
    "label":"Investopedia - Diversification",
    "url":"https://www.investopedia.com/terms/d/diversification.asp"
    }
    ],
    'portfolio_tips':[
    {
    "label":"ICICI - Mutual Fund Guide",
    "url":"https://www.icicibank.com/blogs/mutual-fund/beginners-guide-on-mutual-funds"
    }
    ],
    'market_trends':[
    {
    "label":"OFP Funding - Market Reading",
    "url":"https://ofpfunding.com/read-markets-smart-beginners-guide/"
    }
    ],
    'financial_goals':[
    {
    "label":"Tata Capital - Finance for Beginners",
    "url":"https://tatacapitalmoneyfy.com/blog/investment-guide/finance-for-beginners/"
    }
    ],
    'budgeting':[
    {
    "label":"Upstox - Budgeting Guide",
    "url":"https://upstox.com/news/personal-finance/investing/budgeting-for-beginners-a-step-by-step-guide/article-122313/"
    }
    ],
    'tax_planning':[
    {
    "label":"SEBI - Investor Education",
    "url":"https://investor.sebi.gov.in/"
    },
    {
    "label":"NSE - How to Invest",
    "url":"https://www.nseindia.com/invest/how-to-invest-in-capital-market"
    }
    ]
    }

    def __init__ (self ):
        self .name ="Nex"
        self .role ="Practical Course Mentor"

    def generate_response (self ,request_data :Dict )->Dict :
        """
        Generate structured response based on request
        
        Args:
            request_data: {
                "action": str,
                "lesson_id": str,
                "page_type": str,
                "user_context": dict,
                "requested_depth": str,
                "allow_web_fetch": bool,
                "sources": List[Dict],
                "user_message": str
            }
        
        Returns:
            Structured JSON response
        """
        action =request_data .get ('action','explain')
        lesson_id =request_data .get ('lesson_id','')
        user_context =request_data .get ('user_context',{})
        requested_depth =request_data .get ('requested_depth','medium')
        sources =request_data .get ('sources',[])
        user_message =request_data .get ('user_message','')


        if not sources :
            sources =self ._get_default_sources (lesson_id )


        max_words ={
        'short':50 ,
        'medium':150 ,
        'long':300 
        }.get (requested_depth ,150 )


        if action =='explain':
            return self ._generate_explanation (
            lesson_id ,user_context ,sources ,user_message ,max_words 
            )
        elif action =='quiz':
            return self ._generate_quiz (lesson_id ,sources )
        elif action =='summarize':
            return self ._generate_summary (lesson_id ,sources ,max_words )
        elif action =='compare':
            return self ._generate_comparison (lesson_id ,sources ,max_words )
        elif action =='next_steps':
            return self ._generate_next_steps (lesson_id ,user_context ,sources )
        else :
            return self ._generate_explanation (
            lesson_id ,user_context ,sources ,user_message ,max_words 
            )

    def _generate_explanation (
    self ,lesson_id :str ,user_context :Dict ,
    sources :List [Dict ],user_message :str ,max_words :int 
    )->Dict :
        """Generate explanation response"""

        topic =self ._extract_topic (lesson_id )


        demo_balance =user_context .get ('demo_balance')
        confidence =user_context .get ('confidence_level','med')


        explanations =self ._get_topic_explanations (topic )
        explanation =explanations .get ('main','')


        if demo_balance :
            explanation +=f" With your ₹{demo_balance :,} demo balance, you can start with small, manageable steps."


        explanation =self ._truncate_text (explanation ,max_words )


        bullet_steps =explanations .get ('steps',[])
        if demo_balance :
            bullet_steps =self ._personalize_steps (bullet_steps ,demo_balance )


        title =explanations .get ('title',f'Understanding {topic .replace ("_"," ").title ()}')


        quiz =None 
        if confidence in ['low','med']:
            quiz =self ._generate_simple_quiz (topic )

        return {
        "title":title ,
        "explanation":explanation ,
        "bullet_steps":bullet_steps [:5 ],
        "links":sources [:3 ],
        "quiz":quiz ,
        "apply_actions":{
        "apply_to_demo_portfolio":True if demo_balance else False 
        }
        }

    def _generate_quiz (self ,lesson_id :str ,sources :List [Dict ])->Dict :
        """Generate quiz question"""
        topic =self ._extract_topic (lesson_id )
        quiz =self ._generate_simple_quiz (topic )

        return {
        "title":"Quick Knowledge Check",
        "explanation":"Test your understanding with this quick question.",
        "bullet_steps":[],
        "links":sources [:2 ],
        "quiz":quiz ,
        "apply_actions":{}
        }

    def _generate_summary (self ,lesson_id :str ,sources :List [Dict ],max_words :int )->Dict :
        """Generate summary"""
        topic =self ._extract_topic (lesson_id )
        explanations =self ._get_topic_explanations (topic )
        summary =explanations .get ('summary',explanations .get ('main',''))
        summary =self ._truncate_text (summary ,max_words )

        return {
        "title":f"Summary: {topic .replace ('_',' ').title ()}",
        "explanation":summary ,
        "bullet_steps":explanations .get ('key_points',[])[:3 ],
        "links":sources [:2 ],
        "quiz":None ,
        "apply_actions":{}
        }

    def _generate_comparison (self ,lesson_id :str ,sources :List [Dict ],max_words :int )->Dict :
        """Generate comparison"""
        topic =self ._extract_topic (lesson_id )
        explanations =self ._get_topic_explanations (topic )
        comparison =explanations .get ('comparison','')
        comparison =self ._truncate_text (comparison ,max_words )

        return {
        "title":f"Comparing Options: {topic .replace ('_',' ').title ()}",
        "explanation":comparison ,
        "bullet_steps":[],
        "links":sources [:3 ],
        "quiz":None ,
        "apply_actions":{}
        }

    def _generate_next_steps (self ,lesson_id :str ,user_context :Dict ,sources :List [Dict ])->Dict :
        """Generate next steps"""
        topic =self ._extract_topic (lesson_id )
        explanations =self ._get_topic_explanations (topic )
        steps =explanations .get ('steps',[])

        demo_balance =user_context .get ('demo_balance')
        if demo_balance :
            steps =self ._personalize_steps (steps ,demo_balance )

        return {
        "title":"Your Next Steps",
        "explanation":"Here are concrete actions you can take right now to apply what you've learned.",
        "bullet_steps":steps [:5 ],
        "links":sources [:2 ],
        "quiz":None ,
        "apply_actions":{
        "apply_to_demo_portfolio":True if demo_balance else False 
        }
        }

    def _extract_topic (self ,lesson_id :str )->str :
        """Extract topic from lesson_id"""

        for topic in self .CONCEPT_SOURCES .keys ():
            if topic in lesson_id .lower ():
                return topic 

        return 'investing_basics'

    def _get_default_sources (self ,lesson_id :str )->List [Dict ]:
        """Get default sources for lesson"""
        topic =self ._extract_topic (lesson_id )
        return self .CONCEPT_SOURCES .get (topic ,self .CONCEPT_SOURCES ['investing_basics'])

    def _get_topic_explanations (self ,topic :str )->Dict :
        """Get topic-specific explanations and steps"""
        explanations ={
        'investing_basics':{
        'title':'Understanding Investing Basics',
        'main':'Investing means putting your money to work to generate returns over time. Instead of keeping money idle, you purchase assets that have potential to grow. The key is starting small, staying consistent, and understanding your risk tolerance.',
        'summary':'Investing is about making your money grow through assets like stocks, bonds, and mutual funds. Start with understanding your goals and risk capacity.',
        'steps':[
        'Assess your financial situation: income, expenses, and existing savings',
        'Set clear investment goals (short-term vs long-term)',
        'Build an emergency fund of 3-6 months expenses first',
        'Start with low-risk options like debt funds or balanced mutual funds',
        'Consider SIPs (Systematic Investment Plans) for disciplined investing'
        ],
        'key_points':[
        'Investing beats inflation and grows wealth over time',
        'Start small and increase gradually as you learn',
        'Diversification reduces risk'
        ]
        },
        'safe_sips':{
        'title':'Understanding Safe SIPs',
        'main':'A Systematic Investment Plan (SIP) lets you invest a fixed amount regularly in mutual funds. It removes the need to time the market and builds discipline. Safe SIPs for beginners include large-cap funds, balanced funds, and index funds.',
        'summary':'SIPs are regular, automated investments in mutual funds. They use rupee-cost averaging to reduce market timing risk.',
        'steps':[
        'Choose a large-cap or balanced mutual fund for stability',
        'Start with ₹500-2000 per month (affordable for beginners)',
        'Set up auto-debit from your bank account',
        'Review performance quarterly, but stay invested for 3-5 years minimum',
        'Increase SIP amount as your income grows'
        ],
        'key_points':[
        'SIPs start as low as ₹500/month',
        'Rupee-cost averaging reduces volatility impact',
        'Long-term SIPs (5+ years) show best results'
        ]
        },
        'emergency_fund':{
        'title':'Building Your Emergency Fund',
        'main':'An emergency fund is money set aside for unexpected expenses like medical emergencies, job loss, or urgent repairs. Experts recommend saving 3-6 months of essential expenses. Keep it in easily accessible, low-risk options like savings accounts or liquid mutual funds.',
        'summary':'Emergency fund = 3-6 months of expenses in easily accessible, safe accounts. It\'s your financial safety net.',
        'steps':[
        'Calculate 3 months of essential expenses (rent, food, utilities)',
        'Open a separate savings account or liquid mutual fund',
        'Set up automatic monthly transfers to build the fund',
        'Keep it separate from your regular savings',
        'Rebuild it immediately if you use it'
        ],
        'key_points':[
        '3-6 months expenses is the standard recommendation',
        'Keep in liquid, low-risk accounts only',
        'Use only for true emergencies'
        ]
        },
        'diversification':{
        'title':'Understanding Diversification',
        'main':'Diversification means spreading investments across different assets, sectors, and companies to reduce risk. If one investment performs poorly, others can compensate. A well-diversified portfolio includes equity, debt, and sometimes gold or real estate.',
        'summary':'Diversification spreads risk by investing in multiple assets. Don\'t put all eggs in one basket.',
        'steps':[
        'Allocate across asset classes: equity (60-70%), debt (20-30%), gold (5-10%)',
        'Diversify within equity: large-cap, mid-cap, small-cap funds',
        'Spread across sectors: IT, banking, pharma, FMCG',
        'Consider geography: India + international funds',
        'Rebalance quarterly to maintain target allocation'
        ],
        'key_points':[
        'Reduces portfolio risk significantly',
        'Smoother returns over time',
        '15-20 different investments is optimal'
        ]
        },
        'portfolio_tips':{
        'title':'Portfolio Construction Tips',
        'main':'Building a portfolio requires planning your asset allocation based on goals, timeline, and risk tolerance. A common strategy is age-based: (100 - your age)% in equity. Regular rebalancing keeps your portfolio aligned with your targets.',
        'summary':'Portfolio = planned mix of assets. Allocate based on goals and timeline. Rebalance regularly.',
        'steps':[
        'Define your investment goals and timeline (short/medium/long-term)',
        'Assess risk tolerance (conservative/moderate/aggressive)',
        'Allocate assets: equity for growth, debt for stability',
        'Choose specific funds matching your allocation',
        'Review and rebalance quarterly or when allocation drifts 5%'
        ],
        'key_points':[
        'Age-based rule: (100 - age)% in equity',
        'Rebalance when allocation drifts from target',
        'Tax-efficient investing boosts returns'
        ]
        },
        'market_trends':{
        'title':'Understanding Market Trends',
        'main':'Markets move in cycles: accumulation (smart money buys), markup (prices rise), distribution (smart money sells), and decline (prices fall). Understanding these cycles helps you stay calm during volatility and make rational decisions rather than emotional ones.',
        'summary':'Markets cycle through phases. Understanding cycles helps avoid emotional investing mistakes.',
        'steps':[
        'Learn to identify market phases (bull vs bear markets)',
        'Monitor key indicators: GDP, inflation, interest rates, corporate earnings',
        'Stay invested during downturns (don\'t panic sell)',
        'Use SIPs to benefit from market cycles automatically',
        'Focus on long-term trends, ignore short-term noise'
        ],
        'key_points':[
        'Bull markets last longer than bear markets',
        'Emotional investing is the biggest enemy',
        'Long-term investors benefit from cycles'
        ]
        },
        'financial_goals':{
        'title':'Setting Financial Goals',
        'main':'Clear financial goals guide your investment decisions. Use the SMART framework: Specific, Measurable, Achievable, Relevant, and Time-bound. Prioritize goals: emergency fund first, then high-interest debt, retirement, major purchases, and lifestyle goals.',
        'summary':'SMART goals = Specific, Measurable, Achievable, Relevant, Time-bound. Prioritize and track progress.',
        'steps':[
        'List all financial goals with amounts and deadlines',
        'Prioritize: emergency fund → debt → retirement → major goals',
        'Calculate monthly investment needed for each goal',
        'Choose appropriate investments for each timeline',
        'Review progress quarterly and adjust as needed'
        ],
        'key_points':[
        'SMART framework ensures actionable goals',
        'Match investment type to goal timeline',
        'Regular review keeps you on track'
        ]
        },
        'budgeting':{
        'title':'Budgeting Basics',
        'main':'A budget is a plan for your money that tracks income, expenses, and savings. The 50/30/20 rule suggests: 50% for needs, 30% for wants, 20% for savings and investments. Budgeting gives you control over your finances and helps achieve goals.',
        'summary':'Budget = income vs expenses plan. 50/30/20 rule: needs/wants/savings. Track and adjust monthly.',
        'steps':[
        'Track expenses for 3 months to understand spending patterns',
        'Categorize: fixed (rent, EMI) vs variable (food, entertainment)',
        'Apply 50/30/20 rule or adjust based on your situation',
        'Use apps or spreadsheets to track daily',
        'Review monthly and cut unnecessary expenses'
        ],
        'key_points':[
        '50/30/20: needs/wants/savings split',
        'Track for 3 months to see real patterns',
        'Automate savings before spending'
        ]
        },
        'tax_planning':{
        'title':'Tax Planning Strategies',
        'main':'Tax planning legally optimizes your tax liability through smart investments and deductions. Section 80C allows ₹1.5 lakh deduction through ELSS funds, PPF, EPF, and other options. ELSS funds offer tax benefits with potential for higher returns than traditional tax-savers.',
        'summary':'Tax planning = legal optimization. Section 80C: ₹1.5L deduction. ELSS funds offer best growth potential.',
        'steps':[
        'Maximize Section 80C: invest ₹1.5 lakh in ELSS, PPF, or EPF',
        'Consider ELSS funds for tax savings + growth potential',
        'Hold equity investments 1+ years for long-term capital gains benefit',
        'Use debt funds for short-term goals (indexation benefit)',
        'Plan before March to maximize annual benefits'
        ],
        'key_points':[
        'Section 80C: ₹1.5L deduction available',
        'ELSS: 3-year lock-in, tax benefit + growth',
        'Long-term capital gains: lower tax on equity held 1+ years'
        ]
        }
        }

        return explanations .get (topic ,explanations ['investing_basics'])

    def _generate_simple_quiz (self ,topic :str )->Optional [Dict ]:
        """Generate a simple quiz question for the topic"""
        quizzes ={
        'investing_basics':{
        'question':'What is the primary purpose of investing?',
        'options':[
        'To save money safely',
        'To grow wealth over time',
        'To avoid taxes',
        'To spend money quickly'
        ],
        'correct_index':1 ,
        'explanation':'Investing aims to grow wealth over time by putting money in assets that appreciate in value.'
        },
        'safe_sips':{
        'question':'What is the minimum SIP amount typically allowed?',
        'options':[
        '₹100',
        '₹500',
        '₹1,000',
        '₹5,000'
        ],
        'correct_index':1 ,
        'explanation':'Most mutual funds allow SIPs starting from ₹500 per month, making it accessible for beginners.'
        },
        'emergency_fund':{
        'question':'How many months of expenses should an emergency fund cover?',
        'options':[
        '1 month',
        '3 months',
        '6 months',
        '12 months'
        ],
        'correct_index':2 ,
        'explanation':'Experts recommend 3-6 months of essential expenses. 6 months provides better security.'
        },
        'diversification':{
        'question':'What is the main benefit of diversification?',
        'options':[
        'Higher returns',
        'Reduced risk',
        'Lower taxes',
        'Faster growth'
        ],
        'correct_index':1 ,
        'explanation':'Diversification reduces portfolio risk by spreading investments across different assets.'
        },
        'portfolio_tips':{
        'question':'According to the age-based rule, if you are 30 years old, what percentage should be in equity?',
        'options':[
        '30%',
        '50%',
        '70%',
        '90%'
        ],
        'correct_index':2 ,
        'explanation':'Age-based rule: (100 - age)% in equity. For 30 years: 70% equity, 30% debt.'
        },
        'market_trends':{
        'question':'What should you do during a market downturn?',
        'options':[
        'Sell all investments',
        'Stay invested and continue SIPs',
        'Invest everything at once',
        'Avoid investing completely'
        ],
        'correct_index':1 ,
        'explanation':'Staying invested during downturns and continuing SIPs allows you to buy more units at lower prices.'
        },
        'financial_goals':{
        'question':'What does SMART stand for in goal setting?',
        'options':[
        'Simple, Measurable, Achievable, Realistic, Timely',
        'Specific, Measurable, Achievable, Relevant, Time-bound',
        'Smart, Meaningful, Actionable, Realistic, Timely',
        'Strategic, Measurable, Achievable, Relevant, Timely'
        ],
        'correct_index':1 ,
        'explanation':'SMART = Specific, Measurable, Achievable, Relevant, Time-bound - a proven framework for goal setting.'
        },
        'budgeting':{
        'question':'According to the 50/30/20 rule, what percentage should go to savings?',
        'options':[
        '10%',
        '20%',
        '30%',
        '50%'
        ],
        'correct_index':1 ,
        'explanation':'50/30/20 rule: 50% needs, 30% wants, 20% savings and investments.'
        },
        'tax_planning':{
        'question':'What is the maximum deduction available under Section 80C?',
        'options':[
        '₹50,000',
        '₹1,00,000',
        '₹1,50,000',
        '₹2,00,000'
        ],
        'correct_index':2 ,
        'explanation':'Section 80C allows up to ₹1.5 lakh deduction through ELSS, PPF, EPF, and other eligible investments.'
        }
        }

        return quizzes .get (topic ,quizzes ['investing_basics'])

    def _personalize_steps (self ,steps :List [str ],demo_balance :int )->List [str ]:
        """Personalize steps with demo balance amount"""
        personalized =[]
        for step in steps :

            if '₹'in step and demo_balance :

                if 'SIP'in step or 'month'in step .lower ():
                    step =step .replace ('₹500-2000',f'₹{min (2000 ,demo_balance //25 )}')
                elif 'emergency'in step .lower ():
                    months =3 
                    amount =(demo_balance *0.3 )//months 
                    step =f"Build emergency fund: ₹{int (amount ):,} per month (3 months target)"
            personalized .append (step )
        return personalized if personalized else steps 

    def _truncate_text (self ,text :str ,max_words :int )->str :
        """Truncate text to max_words"""
        words =text .split ()
        if len (words )<=max_words :
            return text 
        return ' '.join (words [:max_words ])+'...'

    def _sanitize_url (self ,url :str )->str :
        """Remove tracking parameters from URL"""
        parsed =urlparse (url )

        query_params =parse_qs (parsed .query )
        filtered_params ={k :v for k ,v in query_params .items ()
        if k not in ['utm_source','utm_medium','utm_campaign','ref','fbclid']}


        new_query ='&'.join ([f"{k }={v [0 ]}"for k ,v in filtered_params .items ()])
        new_url =f"{parsed .scheme }://{parsed .netloc }{parsed .path }"
        if new_query :
            new_url +=f"?{new_query }"
        return new_url 


def add_disclaimer (response :Dict )->Dict :
    """Add educational disclaimer to response"""
    disclaimer ="This is educational demo content — not financial advice."
    if 'explanation'in response :
        response ['explanation']+=f"\n\n*{disclaimer }*"
    return response 

