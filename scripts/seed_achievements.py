from users .models import Achievement 


ALL_ACHIEVEMENTS =[

{'id':'first_trade','name':'First Trade','description':'Execute your first stock trade','icon_name':'briefcase','category':'trading','xp_reward':25 },
{'id':'portfolio_pro','name':'Portfolio Pro','description':'Build a diversified portfolio with 5+ stocks','icon_name':'briefcase','category':'trading','xp_reward':100 },
{'id':'diversified','name':'Diversified Investor','description':'Own stocks across 3+ different sectors','icon_name':'target','category':'trading','xp_reward':75 },
{'id':'risk_taker','name':'Risk Taker','description':'Make a trade worth over ₹10,000','icon_name':'zap','category':'trading','xp_reward':50 },
{'id':'conservative','name':'Conservative Investor','description':'Maintain positive returns for 7+ days','icon_name':'shield','category':'trading','xp_reward':75 },


{'id':'first_lesson','name':'First Lesson','description':'Complete your first course module','icon_name':'book-open','category':'learning','xp_reward':20 },
{'id':'course_complete','name':'Course Graduate','description':'Complete an entire course','icon_name':'award','category':'learning','xp_reward':150 },
{'id':'quiz_ace','name':'Quiz Ace','description':'Score 100% on any course quiz','icon_name':'star','category':'learning','xp_reward':50 },
{'id':'perfect_quiz','name':'Perfect Quiz','description':'Score 80%+ on a scenario quiz','icon_name':'check-circle-2','category':'learning','xp_reward':100 },
{'id':'knowledge_seeker','name':'Knowledge Seeker','description':'Complete 10 course modules','icon_name':'book-open','category':'learning','xp_reward':200 },


{'id':'streak_5','name':'5-Day Streak','description':'Log in and participate for 5 consecutive days','icon_name':'flame','category':'consistency','xp_reward':50 },
{'id':'streak_10','name':'10-Day Streak','description':'Maintain a 10-day activity streak','icon_name':'flame','category':'consistency','xp_reward':100 },
{'id':'streak_30','name':'30-Day Streak','description':'An incredible 30-day streak of learning','icon_name':'flame','category':'consistency','xp_reward':300 },
{'id':'daily_trader','name':'Daily Trader','description':'Make trades on 3 different days','icon_name':'sun','category':'consistency','xp_reward':40 },


{'id':'xp_100','name':'Rising Star','description':'Earn your first 100 XP','icon_name':'sparkles','category':'milestone','xp_reward':25 },
{'id':'xp_500','name':'XP Hunter','description':'Accumulate 500 XP','icon_name':'sparkles','category':'milestone','xp_reward':50 },
{'id':'xp_milestone','name':'XP Legend','description':'Reach 1000 XP and beyond','icon_name':'trophy','category':'milestone','xp_reward':150 },
{'id':'scenario_master','name':'Scenario Master','description':'Complete 5 financial scenario quizzes','icon_name':'target','category':'milestone','xp_reward':100 },
{'id':'stock_predictor','name':'Stock Oracle','description':'Make 10 stock predictions','icon_name':'trending-up','category':'milestone','xp_reward':75 },
{'id':'profit_maker','name':'Profit Maker','description':'Achieve 10% portfolio returns','icon_name':'trending-up','category':'milestone','xp_reward':200 },
]

print ("Seeding achievements...")
for ach in ALL_ACHIEVEMENTS :
    obj ,created =Achievement .objects .get_or_create (
    id =ach ['id'],
    defaults ={
    'name':ach ['name'],
    'description':ach ['description'],
    'icon_name':ach ['icon_name'],
    'category':ach ['category'],
    'xp_reward':ach ['xp_reward'],
    'is_active':True 
    }
    )
    if created :
        print (f"Created: {ach ['id']}")
    else :

        obj .name =ach ['name']
        obj .description =ach ['description']
        obj .icon_name =ach ['icon_name']
        obj .category =ach ['category']
        obj .xp_reward =ach ['xp_reward']
        obj .save ()
        print (f"Updated: {ach ['id']}")

print ("Done.")
