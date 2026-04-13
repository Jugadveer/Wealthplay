"""
ML Data Preparation - Download and prepare stock data with technical features
"""

import yfinance as yf 
import pandas as pd 
import numpy as np 
import json 
from pathlib import Path 


TICKERS =[

"AAPL","GOOGL","MSFT","TSLA","AMZN","META","NVDA","SPY",

"RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","ITC.NS","BHARTIARTL.NS"
]
TICKER_NAMES ={

"AAPL":"Apple Inc.",
"GOOGL":"Alphabet Inc.",
"MSFT":"Microsoft Corporation",
"TSLA":"Tesla Inc.",
"AMZN":"Amazon.com Inc.",
"META":"Meta Platforms Inc.",
"NVDA":"NVIDIA Corporation",
"SPY":"SPDR S&P 500 ETF",

"RELIANCE.NS":"Reliance Industries Limited",
"TCS.NS":"Tata Consultancy Services Limited",
"INFY.NS":"Infosys Limited",
"HDFCBANK.NS":"HDFC Bank Limited",
"ICICIBANK.NS":"ICICI Bank Limited",
"SBIN.NS":"State Bank of India",
"ITC.NS":"ITC Limited",
"BHARTIARTL.NS":"Bharti Airtel Limited"
}


BASE_DIR =Path (__file__ ).resolve ().parent .parent 
OUT_DIR =BASE_DIR /"ml"/"artifacts"
OUT_DIR .mkdir (parents =True ,exist_ok =True )

def compute_rsi (series ,n =14 ):
    """Relative Strength Index"""
    delta =series .diff ()
    up =delta .clip (lower =0 )
    down =-1 *delta .clip (upper =0 )
    ma_up =up .rolling (n ).mean ()
    ma_down =down .rolling (n ).mean ()
    rs =ma_up /(ma_down +1e-9 )
    return 100 -(100 /(1 +rs ))

def prepare_ticker (ticker ,period ="5y",interval ="1d"):
    """Download and prepare features for one ticker"""
    print (f"  Downloading {ticker }...")

    try :
        df =yf .download (ticker ,period =period ,interval =interval ,progress =False ,auto_adjust =True )

        if df .empty :
            print (f"    Warning: No data for {ticker }")
            return None 


        if isinstance (df .columns ,pd .MultiIndex ):
            df .columns =df .columns .get_level_values (0 )

        df =df [['Open','High','Low','Close','Volume']].dropna ()
        df .columns =[str (c ).lower ()for c in df .columns ]


        df ['ret1']=df ['close'].pct_change ()


        for lag in range (1 ,11 ):
            df [f'ret_lag{lag }']=df ['ret1'].shift (lag )


        df ['mom_7']=df ['close'].pct_change (7 )
        df ['mom_21']=df ['close'].pct_change (21 )


        df ['vol_7']=df ['ret1'].rolling (7 ).std ()*(252 **0.5 )
        df ['vol_21']=df ['ret1'].rolling (21 ).std ()*(252 **0.5 )
        df ['vol_63']=df ['ret1'].rolling (63 ).std ()*(252 **0.5 )


        df ['rsi_14']=compute_rsi (df ['close'],14 )


        df ['vma_21']=df ['volume']/(df ['volume'].rolling (21 ).mean ()+1e-9 )
        df ['vma_63']=df ['volume']/(df ['volume'].rolling (63 ).mean ()+1e-9 )


        df ['sma_7']=df ['close'].rolling (7 ).mean ()
        df ['sma_21']=df ['close'].rolling (21 ).mean ()
        df ['sma_50']=df ['close'].rolling (50 ).mean ()


        df ['price_vs_sma7']=df ['close']/(df ['sma_7']+1e-9 )-1 
        df ['price_vs_sma21']=df ['close']/(df ['sma_21']+1e-9 )-1 
        df ['price_vs_sma50']=df ['close']/(df ['sma_50']+1e-9 )-1 


        df ['day_of_week']=df .index .dayofweek 
        df ['month']=df .index .month 


        df .dropna (inplace =True )




        df ['future_ret1']=df ['close'].pct_change ().shift (-1 )
        thr =0.005 
        df ['label_dir']=df ['future_ret1'].apply (
        lambda x :2 if x >thr else (0 if x <-thr else 1 )
        )


        df ['future_vol5']=df ['ret1'].rolling (5 ).std ().shift (-1 )*(252 **0.5 )


        df ['rolling_max']=df ['close'].rolling (63 ).max ()
        df ['drawdown']=(df ['close']-df ['rolling_max'])/df ['rolling_max']


        df ['label_regime']=0 
        df .loc [df ['vol_21']>df ['vol_21'].quantile (0.75 ),'label_regime']=1 
        df .loc [(df ['drawdown']<-0.15 )|(df ['vol_21']>df ['vol_21'].quantile (0.90 )),'label_regime']=2 


        df =df .dropna ()


        df ['ticker']=ticker 
        df ['ticker_name']=TICKER_NAMES .get (ticker ,ticker )

        print (f"    Processed {len (df )} rows")
        return df 

    except Exception as e :
        print (f"    Error: {e }")
        return None 

def build_dataset (tickers =TICKERS ):
    """Build complete dataset from all tickers"""
    print ("Building ML dataset...")
    print ("="*60 )

    frames =[]
    for t in tickers :
        df =prepare_ticker (t )
        if df is not None :
            frames .append (df )

    if not frames :
        print ("ERROR: No data collected!")
        return None ,None 


    df =pd .concat (frames ).reset_index ().rename (columns ={'index':'date'})


    feature_cols =[c for c in df .columns if c .startswith ('ret_lag')or c in [
    'mom_7','mom_21','vol_7','vol_21','vol_63',
    'rsi_14','vma_21','vma_63',
    'price_vs_sma7','price_vs_sma21','price_vs_sma50',
    'day_of_week','month'
    ]]


    df .to_parquet (OUT_DIR /"dataset.parquet")
    print (f"\nSaved dataset: {len (df )} rows, {len (feature_cols )} features")


    with open (OUT_DIR /"feature_cols.json","w")as f :
        json .dump (feature_cols ,f ,indent =2 )
    print (f"Saved feature list: {len (feature_cols )} features")


    ticker_map ={
    ticker .replace ('.NS',''):{
    'full_ticker':ticker ,
    'name':TICKER_NAMES .get (ticker ,ticker ),
    'latest_price':float (df [df ['ticker']==ticker ]['close'].iloc [-1 ])if len (df [df ['ticker']==ticker ])>0 else 0 
    }
    for ticker in tickers 
    }

    with open (OUT_DIR /"ticker_mapping.json","w")as f :
        json .dump (ticker_map ,f ,indent =2 )


    print ("\n"+"="*60 )
    print ("Dataset Summary")
    print ("="*60 )
    print (f"Total samples: {len (df )}")
    date_col ='date'if 'date'in df .columns else df .index .name or 'index'
    if 'date'in df .columns :
        print (f"Date range: {df ['date'].min ()} to {df ['date'].max ()}")
    print (f"Tickers: {df ['ticker'].nunique ()}")
    print (f"\nTarget distributions:")
    print (f"Direction: {df ['label_dir'].value_counts ().to_dict ()}")
    print (f"Regime: {df ['label_regime'].value_counts ().to_dict ()}")
    print (f"\nFeature columns ({len (feature_cols )}):")
    for i ,col in enumerate (feature_cols ,1 ):
        print (f"  {i }. {col }")

    return df ,feature_cols 

if __name__ =="__main__":
    df ,features =build_dataset ()
    if df is not None :
        print ("\n"+"="*60 )
        print ("Data preparation complete!")
        print ("="*60 )
        print ("\nNext steps:")
        print ("  1. Run: python ml/train.py")
        print ("  2. Run: python ml/backtest.py")
