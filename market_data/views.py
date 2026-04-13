from django .http import JsonResponse 
from rest_framework .decorators import api_view ,permission_classes 
from rest_framework .permissions import AllowAny 
import yfinance as yf 

def _stock_fallback_summary (symbol ,title ):
    return (
    f"• {symbol }: {title [:90 ]} suggests fresh information that could move prices in the near term.\n"
    "• Watch whether this changes revenue outlook, margins, or risk sentiment before reacting.\n"
    f"• Use position sizing and a plan-first approach before taking any {symbol } trade. 📊"
    )


def summarize_news (text ,symbol ='AAPL',title =''):
    prompt =f"""You are WEALTHPLAY's friendly financial mentor. Summarize the following news article briefly into exactly 3 easy-to-understand bullet points for a beginner.
Keep the tone friendly and calm. Use one relevant emoji.
Keep the analysis stock-specific for {symbol }.
Mention {symbol } at least once.
News text:
{text }
"""
    try :
        from mentor_engine .gemini_client import gemini_chat 
        response =gemini_chat (prompt ,max_tokens =300 )
        if response and str (response ).strip ():
            return response 
        return _stock_fallback_summary (symbol ,title or "Latest market update")
    except Exception as e :
        print (f"[News] Gemini error: {e }")
        return _stock_fallback_summary (symbol ,title or "Latest market update")

@api_view (['GET'])
@permission_classes ([AllowAny ])
def market_news (request ):
    symbol =request .GET .get ('symbol','AAPL')
    try :
        ticker =yf .Ticker (symbol )
        raw_news =ticker .news 
        if not raw_news :
             return JsonResponse ({'news':[]})

        results =[]
        for article in raw_news [:3 ]:
            title =article .get ('title','')
            publisher =article .get ('publisher','')
            link =article .get ('link','')
            content_to_summarize =(
            f"Symbol: {symbol }\n"
            f"Title: {title }\n"
            f"Publisher: {publisher }\n"
            f"Link: {link }\n"
            "Task: Explain likely impact, key risk, and what a beginner should watch next."
            )
            summary =summarize_news (content_to_summarize ,symbol =symbol ,title =title )

            results .append ({
            'title':title ,
            'link':link ,
            'publisher':publisher ,
            'providerPublishTime':article .get ('providerPublishTime',0 ),
            'summary':summary 
            })

        return JsonResponse ({'news':results })
    except Exception as e :
        return JsonResponse ({'error':str (e )},status =500 )
