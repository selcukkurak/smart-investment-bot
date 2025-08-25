"""
Sentiment Analysis - Piyasa sentiment analizi
News, social media ve market sentiment göstergeleri
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json


@dataclass
class SentimentData:
    """Sentiment veri yapısı"""
    symbol: str
    sentiment_score: float  # -1.0 (very bearish) to 1.0 (very bullish)
    confidence: float       # 0.0 to 1.0
    sources_count: int
    timestamp: datetime
    details: Dict = None


class SentimentAnalysis:
    """
    Sentiment analizi sınıfı
    
    Özellikler:
    - News sentiment analysis
    - Social media sentiment
    - Fear & Greed Index
    - Market sentiment indicators
    - Real-time sentiment tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger('SentimentAnalysis')
        self.sentiment_history = {}
        self.news_sources = []
        self.social_sources = []
        
        # Sentiment keywords
        self.bullish_keywords = [
            'bull', 'bullish', 'buy', 'positive', 'gains', 'rally', 'surge',
            'breakout', 'moon', 'pump', 'strong', 'growth', 'profit', 'uptrend'
        ]
        
        self.bearish_keywords = [
            'bear', 'bearish', 'sell', 'negative', 'losses', 'crash', 'dump',
            'breakdown', 'decline', 'weak', 'correction', 'downtrend', 'fear'
        ]
        
    async def analyze_symbol_sentiment(self, symbol: str,
                                     include_news: bool = True,
                                     include_social: bool = True) -> SentimentData:
        """
        Sembol için genel sentiment analizi
        
        Args:
            symbol: Analiz edilecek sembol
            include_news: Haber analizi dahil edilsin mi
            include_social: Sosyal medya analizi dahil edilsin mi
            
        Returns:
            Sentiment analizi sonucu
        """
        try:
            sentiment_scores = []
            sources_count = 0
            details = {}
            
            # News sentiment
            if include_news:
                news_sentiment = await self._analyze_news_sentiment(symbol)
                if news_sentiment:
                    sentiment_scores.append(news_sentiment['score'])
                    sources_count += news_sentiment['sources_count']
                    details['news'] = news_sentiment
            
            # Social media sentiment (simulated)
            if include_social:
                social_sentiment = await self._analyze_social_sentiment(symbol)
                if social_sentiment:
                    sentiment_scores.append(social_sentiment['score'])
                    sources_count += social_sentiment['sources_count']
                    details['social'] = social_sentiment
            
            # Market indicators sentiment
            market_sentiment = await self._analyze_market_indicators_sentiment(symbol)
            if market_sentiment:
                sentiment_scores.append(market_sentiment['score'])
                sources_count += 1
                details['market_indicators'] = market_sentiment
            
            # Aggregate sentiment
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                confidence = min(1.0, sources_count / 10)  # More sources = higher confidence
            else:
                avg_sentiment = 0.0
                confidence = 0.0
            
            sentiment_data = SentimentData(
                symbol=symbol,
                sentiment_score=avg_sentiment,
                confidence=confidence,
                sources_count=sources_count,
                timestamp=datetime.now(),
                details=details
            )
            
            # Store in history
            if symbol not in self.sentiment_history:
                self.sentiment_history[symbol] = []
            self.sentiment_history[symbol].append(sentiment_data)
            
            # Keep only last 100 records per symbol
            self.sentiment_history[symbol] = self.sentiment_history[symbol][-100:]
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
            return SentimentData(symbol, 0.0, 0.0, 0, datetime.now())
    
    async def _analyze_news_sentiment(self, symbol: str) -> Optional[Dict]:
        """Haber sentiment analizi"""
        try:
            # Simulated news sentiment (gerçek uygulamada news API kullanılır)
            # News API, Alpha Vantage News, or financial news scrapers
            
            # Mock news data
            mock_headlines = [
                f"{symbol} shows strong technical indicators",
                f"Analysts upgrade {symbol} price target",
                f"{symbol} reports better than expected earnings",
                f"Market uncertainty affects {symbol} trading",
                f"{symbol} faces regulatory challenges"
            ]
            
            sentiment_scores = []
            
            for headline in mock_headlines:
                score = self._analyze_text_sentiment(headline)
                sentiment_scores.append(score)
            
            if sentiment_scores:
                avg_score = sum(sentiment_scores) / len(sentiment_scores)
                return {
                    'score': avg_score,
                    'sources_count': len(sentiment_scores),
                    'headlines': mock_headlines,
                    'individual_scores': sentiment_scores
                }
                
        except Exception as e:
            self.logger.error(f"Error in news sentiment analysis: {str(e)}")
            
        return None
    
    async def _analyze_social_sentiment(self, symbol: str) -> Optional[Dict]:
        """Sosyal medya sentiment analizi"""
        try:
            # Simulated social media sentiment
            # Gerçek uygulamada Twitter API, Reddit API kullanılabilir
            
            # Mock social media posts
            mock_posts = [
                f"Just bought more {symbol}, looking bullish! 🚀",
                f"{symbol} is breaking resistance levels",
                f"Not sure about {symbol} right now, might wait",
                f"{symbol} showing weakness, might sell soon",
                f"Long term bullish on {symbol} 📈"
            ]
            
            sentiment_scores = []
            
            for post in mock_posts:
                score = self._analyze_text_sentiment(post)
                sentiment_scores.append(score)
            
            if sentiment_scores:
                avg_score = sum(sentiment_scores) / len(sentiment_scores)
                return {
                    'score': avg_score,
                    'sources_count': len(sentiment_scores),
                    'posts': mock_posts,
                    'individual_scores': sentiment_scores
                }
                
        except Exception as e:
            self.logger.error(f"Error in social sentiment analysis: {str(e)}")
            
        return None
    
    async def _analyze_market_indicators_sentiment(self, symbol: str) -> Optional[Dict]:
        """Market indikatörleri sentiment analizi"""
        try:
            # VIX, Put/Call ratio, etc. bazlı sentiment
            # Simulated market sentiment indicators
            
            sentiment_factors = []
            
            # Simulated VIX level (fear index)
            vix_level = 20 + (hash(symbol) % 30)  # 20-50 range
            if vix_level < 20:
                sentiment_factors.append(0.3)  # Low fear = bullish
            elif vix_level > 40:
                sentiment_factors.append(-0.3)  # High fear = bearish
            else:
                sentiment_factors.append(0.0)  # Neutral
            
            # Simulated Put/Call ratio
            put_call_ratio = 0.5 + (hash(symbol + 'pc') % 100) / 100  # 0.5-1.5 range
            if put_call_ratio < 0.7:
                sentiment_factors.append(0.2)  # Low put/call = bullish
            elif put_call_ratio > 1.2:
                sentiment_factors.append(-0.2)  # High put/call = bearish
            else:
                sentiment_factors.append(0.0)
            
            # Overall market sentiment
            market_sentiment = sum(sentiment_factors) / len(sentiment_factors) if sentiment_factors else 0
            
            return {
                'score': market_sentiment,
                'vix_level': vix_level,
                'put_call_ratio': put_call_ratio,
                'factors': sentiment_factors
            }
            
        except Exception as e:
            self.logger.error(f"Error in market indicators sentiment: {str(e)}")
            
        return None
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """
        Metin sentiment analizi
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            Sentiment skoru (-1.0 to 1.0)
        """
        text_lower = text.lower()
        
        # Keyword counting
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        # Emoji detection
        bullish_emojis = ['🚀', '📈', '💰', '🎯', '✅', '🔥']
        bearish_emojis = ['📉', '❌', '💸', '😰', '🔴', '⬇️']
        
        bullish_emoji_count = sum(1 for emoji in bullish_emojis if emoji in text)
        bearish_emoji_count = sum(1 for emoji in bearish_emojis if emoji in text)
        
        # Total scoring
        total_bullish = bullish_count + bullish_emoji_count
        total_bearish = bearish_count + bearish_emoji_count
        total_signals = total_bullish + total_bearish
        
        if total_signals == 0:
            return 0.0  # Neutral
            
        # Sentiment score
        sentiment = (total_bullish - total_bearish) / total_signals
        
        return max(-1.0, min(1.0, sentiment))
    
    def get_fear_greed_index(self) -> Dict:
        """
        Fear & Greed Index hesaplama
        
        Returns:
            Fear & Greed Index verileri
        """
        # Simulated Fear & Greed Index
        # Gerçek uygulamada CNN Fear & Greed Index API kullanılır
        
        base_score = 50
        
        # Factors affecting fear & greed
        factors = {
            'market_momentum': np.random.uniform(-10, 10),
            'stock_price_strength': np.random.uniform(-10, 10),
            'stock_price_breadth': np.random.uniform(-10, 10),
            'put_call_options': np.random.uniform(-10, 10),
            'junk_bond_demand': np.random.uniform(-10, 10),
            'market_volatility': np.random.uniform(-10, 10),
            'safe_haven_demand': np.random.uniform(-10, 10)
        }
        
        total_adjustment = sum(factors.values())
        fear_greed_score = max(0, min(100, base_score + total_adjustment))
        
        # Classification
        if fear_greed_score >= 75:
            classification = "Extreme Greed"
        elif fear_greed_score >= 55:
            classification = "Greed"
        elif fear_greed_score >= 45:
            classification = "Neutral"
        elif fear_greed_score >= 25:
            classification = "Fear"
        else:
            classification = "Extreme Fear"
        
        return {
            'score': fear_greed_score,
            'classification': classification,
            'factors': factors,
            'timestamp': datetime.now(),
            'interpretation': self._interpret_fear_greed(fear_greed_score)
        }
    
    def _interpret_fear_greed(self, score: float) -> str:
        """Fear & Greed Index yorumlama"""
        if score >= 75:
            return "Market is in extreme greed phase - potential selling opportunity"
        elif score >= 55:
            return "Market shows greed - monitor for reversal signals"
        elif score >= 45:
            return "Market sentiment is neutral - look for directional signals"
        elif score >= 25:
            return "Market shows fear - potential buying opportunity"
        else:
            return "Market is in extreme fear - strong buying opportunity"
    
    def get_sentiment_trend(self, symbol: str, days: int = 7) -> Dict:
        """
        Sentiment trend analizi
        
        Args:
            symbol: Sembol adı
            days: Analiz günü
            
        Returns:
            Sentiment trend bilgileri
        """
        if symbol not in self.sentiment_history:
            return {
                'trend': 'unknown',
                'current_sentiment': 0.0,
                'average_sentiment': 0.0,
                'trend_strength': 0.0
            }
        
        # Son X günlük veri
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sentiments = [
            s for s in self.sentiment_history[symbol]
            if s.timestamp >= cutoff_date
        ]
        
        if len(recent_sentiments) < 2:
            return {
                'trend': 'insufficient_data',
                'current_sentiment': recent_sentiments[0].sentiment_score if recent_sentiments else 0.0,
                'average_sentiment': 0.0,
                'trend_strength': 0.0
            }
        
        # Trend calculation
        scores = [s.sentiment_score for s in recent_sentiments]
        avg_sentiment = sum(scores) / len(scores)
        
        # Linear regression for trend
        x = list(range(len(scores)))
        if len(scores) >= 3:
            slope = np.polyfit(x, scores, 1)[0]
        else:
            slope = scores[-1] - scores[0]
        
        # Trend classification
        if slope > 0.1:
            trend = 'improving'
        elif slope < -0.1:
            trend = 'deteriorating'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'current_sentiment': recent_sentiments[-1].sentiment_score,
            'average_sentiment': avg_sentiment,
            'trend_strength': abs(slope),
            'data_points': len(recent_sentiments),
            'period_days': days
        }
    
    async def get_market_wide_sentiment(self, api_clients: Dict) -> Dict:
        """
        Genel piyasa sentiment analizi
        
        Args:
            api_clients: API client'ları
            
        Returns:
            Genel piyasa sentiment
        """
        try:
            sentiment_data = {}
            
            # Crypto market sentiment
            crypto_sentiment = await self._get_crypto_market_sentiment(
                api_clients.get('binance')
            )
            sentiment_data['crypto'] = crypto_sentiment
            
            # Stock market sentiment
            stock_sentiment = await self._get_stock_market_sentiment(
                api_clients.get('yahoo_finance')
            )
            sentiment_data['stocks'] = stock_sentiment
            
            # Forex sentiment
            forex_sentiment = await self._get_forex_sentiment(
                api_clients.get('alpha_vantage')
            )
            sentiment_data['forex'] = forex_sentiment
            
            # Fear & Greed Index
            fear_greed = self.get_fear_greed_index()
            sentiment_data['fear_greed'] = fear_greed
            
            # Overall market sentiment
            individual_scores = []
            for asset_class, data in sentiment_data.items():
                if asset_class != 'fear_greed' and isinstance(data, dict):
                    score = data.get('sentiment_score', 0)
                    individual_scores.append(score)
            
            overall_sentiment = sum(individual_scores) / len(individual_scores) if individual_scores else 0
            
            return {
                'overall_sentiment': overall_sentiment,
                'overall_classification': self._classify_sentiment(overall_sentiment),
                'asset_classes': sentiment_data,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error in market-wide sentiment analysis: {str(e)}")
            return {
                'overall_sentiment': 0.0,
                'overall_classification': 'neutral',
                'error': str(e)
            }
    
    async def _get_crypto_market_sentiment(self, binance_client) -> Dict:
        """Kripto piyasa sentiment"""
        try:
            if not binance_client:
                return {'sentiment_score': 0.0, 'classification': 'unknown'}
            
            # Top gainers/losers analizi
            gainers_losers = await binance_client.get_top_gainers_losers(20)
            
            gainers = gainers_losers.get('gainers', [])
            losers = gainers_losers.get('losers', [])
            
            # Sentiment calculation
            if gainers and losers:
                avg_gain = sum(g['change_pct'] for g in gainers) / len(gainers)
                avg_loss = sum(abs(l['change_pct']) for l in losers) / len(losers)
                
                # Normalize to -1 to 1 range
                sentiment_score = max(-1.0, min(1.0, (avg_gain - avg_loss) / 10))
            else:
                sentiment_score = 0.0
            
            return {
                'sentiment_score': sentiment_score,
                'classification': self._classify_sentiment(sentiment_score),
                'gainers_count': len(gainers),
                'losers_count': len(losers),
                'avg_gain': avg_gain if gainers else 0,
                'avg_loss': avg_loss if losers else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in crypto sentiment: {str(e)}")
            return {'sentiment_score': 0.0, 'classification': 'unknown'}
    
    async def _get_stock_market_sentiment(self, yahoo_client) -> Dict:
        """Hisse piyasası sentiment"""
        try:
            if not yahoo_client:
                return {'sentiment_score': 0.0, 'classification': 'unknown'}
            
            # Market indices analysis
            indices = await yahoo_client.get_market_indices()
            
            sentiment_scores = []
            
            for symbol, data in indices.items():
                change_pct = data.get('change_percentage', 0)
                # Normalize percentage change to sentiment score
                normalized_score = max(-1.0, min(1.0, change_pct / 5))  # ±5% = ±1.0 sentiment
                sentiment_scores.append(normalized_score)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                'sentiment_score': avg_sentiment,
                'classification': self._classify_sentiment(avg_sentiment),
                'indices_analyzed': len(indices),
                'indices_data': indices
            }
            
        except Exception as e:
            self.logger.error(f"Error in stock sentiment: {str(e)}")
            return {'sentiment_score': 0.0, 'classification': 'unknown'}
    
    async def _get_forex_sentiment(self, alpha_vantage_client) -> Dict:
        """Forex piyasa sentiment"""
        try:
            if not alpha_vantage_client:
                return {'sentiment_score': 0.0, 'classification': 'unknown'}
            
            # Major forex pairs momentum analysis
            major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
            sentiment_scores = []
            
            for pair in major_pairs:
                # Historical data al (rate limit nedeniyle sınırlı)
                historical = await alpha_vantage_client.get_historical_data(pair, 'daily', 5)
                
                if historical and len(historical) >= 2:
                    # 1-day change
                    change = (historical[0]['close'] - historical[1]['close']) / historical[1]['close']
                    normalized_score = max(-1.0, min(1.0, change * 100))  # ±1% = ±1.0 sentiment
                    sentiment_scores.append(normalized_score)
                
                # Rate limit wait
                await asyncio.sleep(12)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                'sentiment_score': avg_sentiment,
                'classification': self._classify_sentiment(avg_sentiment),
                'pairs_analyzed': len(sentiment_scores)
            }
            
        except Exception as e:
            self.logger.error(f"Error in forex sentiment: {str(e)}")
            return {'sentiment_score': 0.0, 'classification': 'unknown'}
    
    def _classify_sentiment(self, score: float) -> str:
        """Sentiment skorunu sınıflandırma"""
        if score >= 0.6:
            return "very_bullish"
        elif score >= 0.2:
            return "bullish"
        elif score >= -0.2:
            return "neutral"
        elif score >= -0.6:
            return "bearish"
        else:
            return "very_bearish"
    
    def get_sentiment_alerts(self, threshold: float = 0.7) -> List[Dict]:
        """
        Sentiment uyarıları
        
        Args:
            threshold: Uyarı eşik değeri
            
        Returns:
            Sentiment uyarıları
        """
        alerts = []
        
        for symbol, history in self.sentiment_history.items():
            if not history:
                continue
                
            latest_sentiment = history[-1]
            
            # Extreme sentiment alerts
            if abs(latest_sentiment.sentiment_score) >= threshold:
                alert_type = "extreme_bullish" if latest_sentiment.sentiment_score > 0 else "extreme_bearish"
                
                alerts.append({
                    'symbol': symbol,
                    'alert_type': alert_type,
                    'sentiment_score': latest_sentiment.sentiment_score,
                    'confidence': latest_sentiment.confidence,
                    'timestamp': latest_sentiment.timestamp,
                    'message': f"{symbol} showing {alert_type.replace('_', ' ')} sentiment ({latest_sentiment.sentiment_score:.2f})"
                })
            
            # Sentiment reversal alerts
            if len(history) >= 3:
                prev_sentiment = history[-3].sentiment_score
                current_sentiment = latest_sentiment.sentiment_score
                
                # Strong reversal (from negative to positive or vice versa)
                if (prev_sentiment < -0.3 and current_sentiment > 0.3) or \
                   (prev_sentiment > 0.3 and current_sentiment < -0.3):
                    
                    reversal_type = "bullish_reversal" if current_sentiment > prev_sentiment else "bearish_reversal"
                    
                    alerts.append({
                        'symbol': symbol,
                        'alert_type': reversal_type,
                        'previous_sentiment': prev_sentiment,
                        'current_sentiment': current_sentiment,
                        'timestamp': latest_sentiment.timestamp,
                        'message': f"{symbol} sentiment reversal detected: {reversal_type.replace('_', ' ')}"
                    })
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return alerts
    
    def get_sentiment_summary(self) -> Dict:
        """
        Sentiment analizi özeti
        
        Returns:
            Genel sentiment özeti
        """
        total_symbols = len(self.sentiment_history)
        
        if total_symbols == 0:
            return {
                'total_symbols_tracked': 0,
                'average_sentiment': 0.0,
                'bullish_symbols': 0,
                'bearish_symbols': 0,
                'neutral_symbols': 0
            }
        
        # Latest sentiments
        latest_sentiments = []
        for symbol, history in self.sentiment_history.items():
            if history:
                latest_sentiments.append(history[-1].sentiment_score)
        
        avg_sentiment = sum(latest_sentiments) / len(latest_sentiments) if latest_sentiments else 0
        
        # Classification counts
        bullish_count = sum(1 for s in latest_sentiments if s > 0.2)
        bearish_count = sum(1 for s in latest_sentiments if s < -0.2)
        neutral_count = total_symbols - bullish_count - bearish_count
        
        return {
            'total_symbols_tracked': total_symbols,
            'average_sentiment': avg_sentiment,
            'average_classification': self._classify_sentiment(avg_sentiment),
            'bullish_symbols': bullish_count,
            'bearish_symbols': bearish_count,
            'neutral_symbols': neutral_count,
            'sentiment_distribution': {
                'bullish_pct': bullish_count / total_symbols if total_symbols > 0 else 0,
                'bearish_pct': bearish_count / total_symbols if total_symbols > 0 else 0,
                'neutral_pct': neutral_count / total_symbols if total_symbols > 0 else 0
            }
        }