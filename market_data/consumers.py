import json 
import asyncio 
import yfinance as yf 
from channels .generic .websocket import AsyncWebsocketConsumer 

class MarketDataConsumer (AsyncWebsocketConsumer ):
    async def connect (self ):
        await self .accept ()
        self .running =True 

        self .symbols =['^NSEI','^GSPC','RELIANCE.NS','AAPL','BTC-USD']
        self .task =asyncio .create_task (self .send_market_data ())

    async def disconnect (self ,close_code ):
        self .running =False 
        if hasattr (self ,'task'):
            self .task .cancel ()

    async def receive (self ,text_data ):
        try :
            data =json .loads (text_data )
            if data .get ('action')=='set_symbols':
                self .symbols =data .get ('symbols',self .symbols )

                prices =await asyncio .to_thread (self ._fetch_prices )
                await self .send (text_data =json .dumps ({'type':'prices','data':prices }))
        except json .JSONDecodeError :
            pass 

    async def send_market_data (self ):
        while self .running :
            try :

                data =await asyncio .to_thread (self ._fetch_prices )
                await self .send (text_data =json .dumps ({'type':'prices','data':data }))
            except asyncio .CancelledError :
                break 
            except Exception as e :
                print (f"[MarketData] Error: {e }")
            await asyncio .sleep (5 )

    def _fetch_prices (self ):
        if not self .symbols :
            return {}
        result ={}
        try :
            tickers =yf .Tickers (" ".join (self .symbols ))
            for sym in self .symbols :
                try :

                    info =tickers .tickers [sym ].fast_info 
                    if info and hasattr (info ,'last_price')and info .last_price is not None :
                        result [sym ]={
                        'price':info .last_price ,
                        'change':info .last_price -info .previous_close ,
                        'percent':((info .last_price /info .previous_close )-1 )*100 if info .previous_close else 0 ,
                        }
                except Exception :
                    pass 
        except Exception as e :
             print (f"[MarketData] Tickers fetch error: {e }")
        return result 
