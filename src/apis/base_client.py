"""
Base API Client - Temel API sınıfı
Tüm API client'ları için ortak interface
"""

import aiohttp
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging


@dataclass
class RateLimit:
    """Rate limiting bilgileri"""
    calls_per_minute: int
    calls_per_hour: int
    last_call_time: float = 0
    calls_this_minute: int = 0
    calls_this_hour: int = 0


class BaseAPIClient(ABC):
    """
    Temel API Client sınıfı
    
    Tüm API client'ları bu sınıftan türeyecek
    Ortak özelliker:
    - Rate limiting
    - Error handling
    - Retry logic
    - Logging
    """
    
    def __init__(self, base_url: str, api_key: str = None, 
                 rate_limit: RateLimit = None):
        """
        Base client başlatma
        
        Args:
            base_url: API base URL
            api_key: API anahtarı
            rate_limit: Rate limiting ayarları
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit or RateLimit(calls_per_minute=60, calls_per_hour=1000)
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Request statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.last_error = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
        
    async def _create_session(self) -> None:
        """HTTP session oluşturma"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
    async def _close_session(self) -> None:
        """HTTP session kapatma"""
        if self.session and not self.session.closed:
            await self.session.close()
            
    def _check_rate_limit(self) -> bool:
        """
        Rate limit kontrolü
        
        Returns:
            Request yapılabilir mi
        """
        current_time = time.time()
        
        # Dakika bazında reset
        if current_time - self.rate_limit.last_call_time > 60:
            self.rate_limit.calls_this_minute = 0
            
        # Saat bazında reset
        if current_time - self.rate_limit.last_call_time > 3600:
            self.rate_limit.calls_this_hour = 0
            
        # Limit kontrol
        if (self.rate_limit.calls_this_minute >= self.rate_limit.calls_per_minute or
            self.rate_limit.calls_this_hour >= self.rate_limit.calls_per_hour):
            return False
            
        return True
    
    async def _wait_for_rate_limit(self) -> None:
        """Rate limit için bekleme"""
        if not self._check_rate_limit():
            wait_time = 60 - (time.time() - self.rate_limit.last_call_time) % 60
            self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
    
    def _update_rate_limit_counters(self) -> None:
        """Rate limit sayaçlarını güncelleme"""
        self.rate_limit.last_call_time = time.time()
        self.rate_limit.calls_this_minute += 1
        self.rate_limit.calls_this_hour += 1
    
    async def _make_request(self, method: str, endpoint: str, 
                          params: Dict = None, data: Dict = None,
                          headers: Dict = None, retry_count: int = 3) -> Dict:
        """
        HTTP request yapma
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Request headers
            retry_count: Retry sayısı
            
        Returns:
            API response
        """
        await self._create_session()
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Default headers
        request_headers = {
            'User-Agent': 'SmartInvestmentBot/1.0',
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            request_headers.update(self._get_auth_headers())
            
        if headers:
            request_headers.update(headers)
            
        for attempt in range(retry_count + 1):
            try:
                self.total_requests += 1
                self._update_rate_limit_counters()
                
                async with self.session.request(
                    method, url, params=params, json=data, headers=request_headers
                ) as response:
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return {
                            'success': True,
                            'data': response_data,
                            'status_code': response.status
                        }
                    elif response.status == 429:  # Rate limit
                        wait_time = int(response.headers.get('Retry-After', 60))
                        self.logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        self.failed_requests += 1
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}: {response_data}',
                            'status_code': response.status
                        }
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < retry_count:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except Exception as e:
                self.failed_requests += 1
                self.last_error = str(e)
                self.logger.error(f"Request error: {str(e)}")
                
                if attempt < retry_count:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded'
        }
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Authentication headers
        Her API için farklı olacak
        
        Returns:
            Auth headers
        """
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Fiyat bilgisi alma
        
        Args:
            symbol: Sembol adı
            
        Returns:
            Fiyat (None ise hata)
        """
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, timeframe: str,
                                limit: int = 100) -> Optional[List[Dict]]:
        """
        Geçmiş veri alma
        
        Args:
            symbol: Sembol adı
            timeframe: Zaman dilimi (1m, 5m, 1h, 1d, etc.)
            limit: Veri sayısı limiti
            
        Returns:
            Historical data list
        """
        pass
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Birden fazla sembol için fiyat alma
        
        Args:
            symbols: Sembol listesi
            
        Returns:
            {symbol: price} dictionary
        """
        prices = {}
        
        # Concurrent requests for better performance
        tasks = [self.get_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error getting price for {symbol}: {result}")
                prices[symbol] = None
            else:
                prices[symbol] = result
                
        return prices
    
    def get_client_stats(self) -> Dict:
        """
        Client istatistikleri
        
        Returns:
            İstatistik bilgileri
        """
        success_rate = (
            (self.total_requests - self.failed_requests) / self.total_requests
            if self.total_requests > 0 else 0
        )
        
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': success_rate,
            'last_error': self.last_error,
            'rate_limit': {
                'calls_this_minute': self.rate_limit.calls_this_minute,
                'calls_this_hour': self.rate_limit.calls_this_hour,
                'limit_per_minute': self.rate_limit.calls_per_minute,
                'limit_per_hour': self.rate_limit.calls_per_hour
            }
        }
    
    async def health_check(self) -> Dict:
        """
        API health check
        
        Returns:
            Health status
        """
        try:
            # Simple ping test
            start_time = time.time()
            result = await self._make_request('GET', '/ping')
            response_time = (time.time() - start_time) * 1000
            
            return {
                'healthy': result['success'],
                'response_time_ms': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }