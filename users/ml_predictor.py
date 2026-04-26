# ML Prediction Service - Adapted from ML repo predictor.py

import yfinance as yf
import pandas as pd
import numpy as np
import json
from pathlib import Path
import os
import sys
from django.conf import settings

# --- Configuration ---
TICKERS = [
    "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "SPY",
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "BHARTIARTL"
]
NSE_TICKERS = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "BHARTIARTL"]

# Paths relative to Django BASE_DIR
ML_ROOT = Path(settings.BASE_DIR)
ARTIFACTS_DIR = ML_ROOT / "ml" / "artifacts"
MODELS_DIR = ML_ROOT / "ml" / "models"


class PredictorService:
    """Handles loading models and making predictions - matches ML repo implementation"""
    
    def __init__(self):
        self.models_loaded = False
        self.dir_model = None
        self.vol_model = None
        self.regime_model = None
        self.features = None
        self.ticker_mapping = None
        self._load_models()

    def _load_models(self):
        try:
            # Skip heavy loading during migrations to prevent crashes/hangs
            if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'showmigrations', 'check']):
                print("[ML] Skipping model load for management command")
                self.models_loaded = False
                return

            # Attempt to load LightGBM.
            try:
                import lightgbm as lgb
            except Exception as e:
                print(f"[ML] LightGBM unavailable: {e}")
                self.models_loaded = False
                return
            except Exception as e:
                print(f"[ML] LightGBM unavailable: {e}")
                self.models_loaded = False
                return

            # Load models
            if (MODELS_DIR / "dir_model.txt").exists():
                try:
                    self.dir_model = lgb.Booster(model_file=str(MODELS_DIR / "dir_model.txt"))
                    print(f"[ML] Loaded direction model")
                except Exception as e:
                    print(f"[ML] Direction model load failed: {e}")
                    self.dir_model = None

            if (MODELS_DIR / "vol_model.txt").exists():
                try:
                    self.vol_model = lgb.Booster(model_file=str(MODELS_DIR / "vol_model.txt"))
                    print(f"[ML] Loaded volatility model")
                except Exception as e:
                    print(f"[ML] Volatility model load failed: {e}")
                    self.vol_model = None

            if (MODELS_DIR / "regime_model.txt").exists():
                try:
                    self.regime_model = lgb.Booster(model_file=str(MODELS_DIR / "regime_model.txt"))
                    print(f"[ML] Loaded regime model")
                except Exception as e:
                    print(f"[ML] Regime model load failed: {e}")
                    self.regime_model = None

            # Load feature list
            if (ARTIFACTS_DIR / "feature_cols.json").exists():
                with open(ARTIFACTS_DIR / "feature_cols.json") as f:
                    self.features = json.load(f)
                print(f"[ML] Loaded {len(self.features)} features")

            # Load ticker mapping
            if (ARTIFACTS_DIR / "ticker_mapping.json").exists():
                with open(ARTIFACTS_DIR / "ticker_mapping.json") as f:
                    self.ticker_mapping = json.load(f)

            self.models_loaded = (
                self.dir_model is not None and
                self.vol_model is not None and
                self.regime_model is not None and
                self.features is not None
            )

            if self.models_loaded:
                print(f"[ML] All models loaded successfully: {len(self.features)} features")
            else:
                print("[ML] Warning: Some ML models not loaded - predictions will use fallback")

        except Exception as e:
            print(f"[ML] Error loading models: {e}")
            import traceback
            traceback.print_exc()
            self.models_loaded = False

    def _get_full_ticker(self, symbol):
        """Convert ticker name to yfinance format (NASDAQ or NSE)"""
        # NASDAQ stocks - use directly
        nasdaq_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'SPY']
        if symbol.upper() in nasdaq_tickers:
            return symbol
        
        # NSE stocks - add .NS suffix
        nse_tickers = {
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS',
            'INFY': 'INFY.NS',
            'INFOSYS': 'INFY.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'SBIN': 'SBIN.NS',
            'ITC': 'ITC.NS',
            'BHARTIARTL': 'BHARTIARTL.NS',
            'BHARTI': 'BHARTIARTL.NS'
        }
        if symbol.upper() in nse_tickers:
            return nse_tickers[symbol.upper()]
        
        # If already has .NS, use as is
        if symbol.endswith('.NS'):
            return symbol
        
        # Fallback to NASDAQ
        return symbol

    def _compute_features(self, ticker_symbol):
        """Download latest data and compute features for a ticker"""
        try:
            # Download last 90 days of data
            df = yf.download(ticker_symbol, period="90d", interval="1d", progress=False, auto_adjust=True)

            if df.empty:
                print(f"[FEATURES] No data for {ticker_symbol}")
                return None

            # Handle multi-index columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            df.columns = [c.lower() for c in df.columns]

            # Compute returns
            df['ret1'] = df['close'].pct_change()

            # Lag returns (1-10 days)
            for lag in range(1, 11):
                df[f'ret_lag{lag}'] = df['ret1'].shift(lag)

            # Momentum features
            df['mom_7'] = df['close'].pct_change(7)
            df['mom_21'] = df['close'].pct_change(21)

            # Volatility features (annualized)
            df['vol_7'] = df['ret1'].rolling(7).std() * np.sqrt(252)
            df['vol_21'] = df['ret1'].rolling(21).std() * np.sqrt(252)
            df['vol_63'] = df['ret1'].rolling(63).std() * np.sqrt(252)

            # RSI
            delta = df['close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            ma_up = up.rolling(14).mean()
            ma_down = down.rolling(14).mean()
            rs = ma_up / (ma_down + 1e-9)
            df['rsi_14'] = 100 - (100 / (1 + rs))

            # Volume features
            df['vma_21'] = df['volume'] / (df['volume'].rolling(21).mean() + 1e-9)
            df['vma_63'] = df['volume'] / (df['volume'].rolling(63).mean() + 1e-9)

            # Price vs SMA
            df['sma_7'] = df['close'].rolling(7).mean()
            df['sma_21'] = df['close'].rolling(21).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['price_vs_sma7'] = df['close'] / (df['sma_7'] + 1e-9) - 1
            df['price_vs_sma21'] = df['close'] / (df['sma_21'] + 1e-9) - 1
            df['price_vs_sma50'] = df['close'] / (df['sma_50'] + 1e-9) - 1

            # Calendar features
            df['day_of_week'] = df.index.dayofweek
            df['month'] = df.index.month

            # Ensure all required features exist
            if not self.features:
                print(f"[FEATURES] Error: Features list is None!")
                return None
                
            missing_features = [f for f in self.features if f not in df.columns]
            if missing_features:
                print(f"[FEATURES] Warning: Missing features for {ticker_symbol}: {missing_features}")
                return None

            df_clean = df[self.features].dropna()

            if df_clean.empty:
                print(f"[FEATURES] Warning: No valid data after feature computation for {ticker_symbol}")
                return None

            # Return latest feature vector
            feature_vector = df_clean.iloc[-1].values
            
            # Validate feature vector
            if np.any(np.isnan(feature_vector)) or np.any(np.isinf(feature_vector)):
                print(f"[FEATURES] Warning: Invalid feature values for {ticker_symbol}")
                return None
                
            return feature_vector

        except Exception as e:
            print(f"[FEATURES] Error computing features for {ticker_symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def predict(self, symbol):
        """
        Get ML predictions for a stock ticker
        Returns dict with direction, volatility, regime predictions
        """
        # Re-check models_loaded
        if not self.models_loaded:
            self._load_models()
            if not self.models_loaded:
                return self._fallback_prediction()

        try:
            # Get ticker symbol
            ticker_symbol = self._get_full_ticker(symbol)

            # Compute features from latest data
            features = self._compute_features(ticker_symbol)

            if features is None:
                print(f"[PREDICT] Features are None, returning fallback")
                return self._fallback_prediction()

            # Reshape for prediction
            X = features.reshape(1, -1)
            
            # Validate feature count
            if len(features) != len(self.features):
                print(f"[PREDICT] Error: Feature count mismatch. Expected {len(self.features)}, got {len(features)}")
                return self._fallback_prediction()

            # Get predictions from all 3 models
            try:
                dir_probs = self.dir_model.predict(X)[0]
                vol_pred = self.vol_model.predict(X)[0]
                regime_probs = self.regime_model.predict(X)[0]
                
                # Ensure probabilities are valid
                if np.any(np.isnan(dir_probs)) or np.any(np.isinf(dir_probs)):
                    print(f"[PREDICT] Warning: Invalid direction probabilities for {symbol}")
                    return self._fallback_prediction()
                    
            except Exception as e:
                print(f"[PREDICT] Error during model prediction for {symbol}: {e}")
                import traceback
                traceback.print_exc()
                return self._fallback_prediction()

            # Direction prediction (0=Down, 1=Neutral, 2=Up)
            dir_class = dir_probs.argmax()
            dir_labels = ['bearish', 'neutral', 'bullish']  # Map to our format
            direction = dir_labels[dir_class]
            dir_confidence = float(dir_probs[dir_class])

            # Regime prediction (0=Calm, 1=Volatile, 2=Crash)
            regime_class = regime_probs.argmax()
            regime_labels = ['Calm', 'Volatile', 'Crash']
            regime = regime_labels[regime_class]

            return {
                'direction': direction,
                'confidence': dir_confidence,
                'vol': float(vol_pred),
                'regime': regime,
            }

        except Exception as e:
            print(f"[PREDICT] Error in prediction: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_prediction()

    def _fallback_prediction(self):
        """Return neutral prediction when models not available"""
        return {
            'direction': 'neutral',
            'confidence': 0.5,
            'regime': 'Calm',
            'vol': 0.02,
        }


# Initialize the service globally to load models once
ML_PREDICTOR = PredictorService()


def get_stock_price(symbol):
    """Simple wrapper to get current price for any symbol"""
    ticker_name = ML_PREDICTOR._get_full_ticker(symbol)
    try:
        ticker = yf.Ticker(ticker_name)
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
    return 0.0


def get_stock_info(symbol, use_cache=True, allow_live_fetch=True):
    """Get basic stock info: price, name, change, etc."""
    # This is a simplified version of what might be in views.py
    ticker_name = ML_PREDICTOR._get_full_ticker(symbol)
    try:
        ticker = yf.Ticker(ticker_name)
        info = ticker.info
        hist = ticker.history(period='2d')
        
        current_price = 0.0
        change_pct = 0.0
        
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
            if len(hist) > 1:
                prev_close = float(hist['Close'].iloc[-2])
                change_pct = ((current_price - prev_close) / prev_close) * 100

        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'current_price': round(current_price, 2),
            'change_percent': round(change_pct, 2),
            'sector': info.get('sector', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', 'INR' if '.NS' in ticker_name else 'USD')
        }
    except Exception as e:
        print(f"[ML] Error fetching info for {symbol}: {e}")
        return {
            'symbol': symbol,
            'name': symbol,
            'current_price': 0.0,
            'change_percent': 0.0,
            'sector': 'N/A',
            'market_cap': 0,
            'currency': 'USD'
        }
