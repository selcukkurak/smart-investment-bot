"""
Notifications - Telegram/Discord bildirimleri
Real-time bildirim sistemi
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json


class TelegramNotifier:
    """
    Telegram bot bildirimleri
    
    Özellikler:
    - Trading alerts
    - Performance reports
    - Risk warnings
    - Custom messages
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Telegram notifier başlatma
        
        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = logging.getLogger('TelegramNotifier')
        
    async def send_message(self, message: str, parse_mode: str = 'HTML',
                          disable_notification: bool = False) -> bool:
        """
        Telegram mesajı gönderme
        
        Args:
            message: Mesaj içeriği
            parse_mode: Parse modu (HTML, Markdown)
            disable_notification: Sessiz bildirim
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram API error: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    async def send_trade_alert(self, trade_data: Dict) -> bool:
        """
        Trade uyarısı gönderme
        
        Args:
            trade_data: Trade bilgileri
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            trade_type = trade_data.get('trade_type', 'UNKNOWN')
            symbol = trade_data.get('symbol', 'UNKNOWN')
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            strategy = trade_data.get('strategy', 'manual')
            profit_loss = trade_data.get('profit_loss', 0)
            
            # Emoji seçimi
            emoji = "🟢" if trade_type == 'BUY' else "🔴"
            pnl_emoji = "💰" if profit_loss > 0 else "💸" if profit_loss < 0 else "➖"
            
            message = f"""
{emoji} <b>Trade Executed</b>

📊 <b>{trade_type}</b> {amount} {symbol}
💵 Price: ${price:.4f}
🎯 Strategy: {strategy}
{pnl_emoji} P&L: ${profit_loss:.2f}

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending trade alert: {str(e)}")
            return False
    
    async def send_performance_report(self, performance_data: Dict) -> bool:
        """
        Performans raporu gönderme
        
        Args:
            performance_data: Performans bilgileri
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            total_value = performance_data.get('total_value', 0)
            total_return = performance_data.get('total_return', 0)
            total_return_pct = performance_data.get('total_return_pct', 0)
            daily_return = performance_data.get('daily_return', 0)
            win_rate = performance_data.get('win_rate', 0)
            
            trend_emoji = "📈" if total_return > 0 else "📉" if total_return < 0 else "➖"
            
            message = f"""
📊 <b>Daily Performance Report</b>

💼 Portfolio Value: ${total_value:.2f}
{trend_emoji} Total Return: ${total_return:.2f} ({total_return_pct:+.2%})
📅 Today's Return: {daily_return:+.2%}
🎯 Win Rate: {win_rate:.1%}

⏰ Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending performance report: {str(e)}")
            return False
    
    async def send_risk_warning(self, risk_data: Dict) -> bool:
        """
        Risk uyarısı gönderme
        
        Args:
            risk_data: Risk bilgileri
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            risk_level = risk_data.get('risk_level', 'unknown')
            risk_score = risk_data.get('risk_score', 0)
            portfolio_risk = risk_data.get('portfolio_risk', 0)
            
            emoji = "🚨" if risk_level in ['high', 'extreme'] else "⚠️"
            
            message = f"""
{emoji} <b>Risk Warning</b>

🔴 Risk Level: {risk_level.upper()}
📊 Risk Score: {risk_score:.1f}/10
💹 Portfolio Risk: {portfolio_risk:.1%}

⚠️ Action may be required!

⏰ Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending risk warning: {str(e)}")
            return False


class DiscordNotifier:
    """
    Discord webhook bildirimleri
    
    Özellikler:
    - Rich embeds
    - Color coding
    - Multiple webhooks
    - Rate limiting
    """
    
    def __init__(self, webhook_url: str):
        """
        Discord notifier başlatma
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger('DiscordNotifier')
        
    async def send_embed(self, title: str, description: str,
                        color: int = 0x00ff00, fields: List[Dict] = None) -> bool:
        """
        Discord embed mesajı gönderme
        
        Args:
            title: Başlık
            description: Açıklama
            color: Renk kodu
            fields: Ek alanlar
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            embed = {
                'title': title,
                'description': description,
                'color': color,
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': 'Smart Investment Bot'
                }
            }
            
            if fields:
                embed['fields'] = fields
            
            data = {
                'embeds': [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data) as response:
                    if response.status == 204:  # Discord success code
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Discord webhook error: {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Discord embed: {str(e)}")
            return False
    
    async def send_trade_notification(self, trade_data: Dict) -> bool:
        """
        Trade bildirimi gönderme
        
        Args:
            trade_data: Trade bilgileri
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            trade_type = trade_data.get('trade_type', 'UNKNOWN')
            symbol = trade_data.get('symbol', 'UNKNOWN')
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            profit_loss = trade_data.get('profit_loss', 0)
            
            # Color coding
            color = 0x00ff00 if trade_type == 'BUY' else 0xff0000  # Green for BUY, Red for SELL
            
            fields = [
                {
                    'name': 'Symbol',
                    'value': symbol,
                    'inline': True
                },
                {
                    'name': 'Type',
                    'value': trade_type,
                    'inline': True
                },
                {
                    'name': 'Amount',
                    'value': str(amount),
                    'inline': True
                },
                {
                    'name': 'Price',
                    'value': f"${price:.4f}",
                    'inline': True
                },
                {
                    'name': 'Strategy',
                    'value': trade_data.get('strategy', 'manual'),
                    'inline': True
                },
                {
                    'name': 'P&L',
                    'value': f"${profit_loss:.2f}",
                    'inline': True
                }
            ]
            
            return await self.send_embed(
                title="Trade Executed",
                description=f"{trade_type} {amount} {symbol} at ${price:.4f}",
                color=color,
                fields=fields
            )
            
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {str(e)}")
            return False
    
    async def send_performance_summary(self, performance_data: Dict) -> bool:
        """
        Performans özeti gönderme
        
        Args:
            performance_data: Performans bilgileri
            
        Returns:
            Gönderim başarılı mı
        """
        try:
            total_value = performance_data.get('total_value', 0)
            total_return_pct = performance_data.get('total_return_pct', 0)
            daily_return = performance_data.get('daily_return', 0)
            
            # Color based on performance
            if total_return_pct > 0:
                color = 0x00ff00  # Green
            elif total_return_pct < 0:
                color = 0xff0000  # Red
            else:
                color = 0xffff00  # Yellow
            
            fields = [
                {
                    'name': 'Portfolio Value',
                    'value': f"${total_value:.2f}",
                    'inline': True
                },
                {
                    'name': 'Total Return',
                    'value': f"{total_return_pct:+.2%}",
                    'inline': True
                },
                {
                    'name': 'Daily Return',
                    'value': f"{daily_return:+.2%}",
                    'inline': True
                },
                {
                    'name': 'Win Rate',
                    'value': f"{performance_data.get('win_rate', 0):.1%}",
                    'inline': True
                },
                {
                    'name': 'Active Positions',
                    'value': str(performance_data.get('active_positions', 0)),
                    'inline': True
                },
                {
                    'name': 'Today\'s Trades',
                    'value': str(performance_data.get('daily_trades', 0)),
                    'inline': True
                }
            ]
            
            return await self.send_embed(
                title="Performance Summary",
                description="Daily portfolio performance update",
                color=color,
                fields=fields
            )
            
        except Exception as e:
            self.logger.error(f"Error sending performance summary: {str(e)}")
            return False


class NotificationManager:
    """
    Bildirim yönetim sınıfı
    
    Özellikler:
    - Multiple channels (Telegram, Discord)
    - Message queuing
    - Rate limiting
    - Priority handling
    - Retry logic
    """
    
    def __init__(self, config: Dict = None):
        """
        Notification manager başlatma
        
        Args:
            config: Bildirim konfigürasyonu
        """
        self.config = config or {}
        self.telegram_notifier = None
        self.discord_notifier = None
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.logger = logging.getLogger('NotificationManager')
        
        # Initialize notifiers
        self._initialize_notifiers()
        
    def _initialize_notifiers(self) -> None:
        """Notifier'ları başlatma"""
        # Telegram
        telegram_config = self.config.get('telegram', {})
        if (telegram_config.get('enabled', False) and 
            telegram_config.get('bot_token') and 
            telegram_config.get('chat_id')):
            
            self.telegram_notifier = TelegramNotifier(
                telegram_config['bot_token'],
                telegram_config['chat_id']
            )
            self.logger.info("Telegram notifier initialized")
        
        # Discord
        discord_config = self.config.get('discord', {})
        if (discord_config.get('enabled', False) and 
            discord_config.get('webhook_url')):
            
            self.discord_notifier = DiscordNotifier(
                discord_config['webhook_url']
            )
            self.logger.info("Discord notifier initialized")
    
    async def start_notification_service(self) -> None:
        """Bildirim servisini başlatma"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("🔔 Notification service started")
        
        # Message processing loop
        while self.is_running:
            try:
                # Get message from queue (with timeout)
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=10.0
                )
                
                await self._process_notification(message)
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                # No messages in queue, continue
                continue
            except Exception as e:
                self.logger.error(f"Error processing notification: {str(e)}")
    
    async def stop_notification_service(self) -> None:
        """Bildirim servisini durdurma"""
        self.is_running = False
        self.logger.info("🔕 Notification service stopped")
    
    async def _process_notification(self, notification: Dict) -> None:
        """Bildirimi işleme"""
        notification_type = notification.get('type')
        priority = notification.get('priority', 'normal')
        
        try:
            if notification_type == 'trade':
                await self._send_trade_notification(notification['data'])
            elif notification_type == 'performance':
                await self._send_performance_notification(notification['data'])
            elif notification_type == 'risk':
                await self._send_risk_notification(notification['data'])
            elif notification_type == 'signal':
                await self._send_signal_notification(notification['data'])
            elif notification_type == 'custom':
                await self._send_custom_notification(notification['data'])
            
            # Rate limiting
            if priority != 'high':
                await asyncio.sleep(1)  # 1 second between normal notifications
                
        except Exception as e:
            self.logger.error(f"Error processing {notification_type} notification: {str(e)}")
    
    async def _send_trade_notification(self, trade_data: Dict) -> None:
        """Trade bildirimi gönderme"""
        tasks = []
        
        if self.telegram_notifier:
            tasks.append(self.telegram_notifier.send_trade_alert(trade_data))
        
        if self.discord_notifier:
            tasks.append(self.discord_notifier.send_trade_notification(trade_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_performance_notification(self, performance_data: Dict) -> None:
        """Performans bildirimi gönderme"""
        tasks = []
        
        if self.telegram_notifier:
            tasks.append(self.telegram_notifier.send_performance_report(performance_data))
        
        if self.discord_notifier:
            tasks.append(self.discord_notifier.send_performance_summary(performance_data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_risk_notification(self, risk_data: Dict) -> None:
        """Risk bildirimi gönderme"""
        if self.telegram_notifier:
            await self.telegram_notifier.send_risk_warning(risk_data)
    
    async def _send_signal_notification(self, signal_data: Dict) -> None:
        """Sinyal bildirimi gönderme"""
        if not self.telegram_notifier:
            return
            
        try:
            symbol = signal_data.get('symbol', 'UNKNOWN')
            signal_type = signal_data.get('signal_type', 'UNKNOWN')
            confidence = signal_data.get('confidence', 0)
            price = signal_data.get('price', 0)
            strategy = signal_data.get('strategy', 'unknown')
            
            signal_emoji = "🟢" if 'BUY' in signal_type else "🔴" if 'SELL' in signal_type else "🔵"
            
            message = f"""
{signal_emoji} <b>Trading Signal</b>

📊 {signal_type} {symbol}
💵 Price: ${price:.4f}
🎯 Confidence: {confidence:.1%}
📈 Strategy: {strategy}

⏰ Generated: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await self.telegram_notifier.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {str(e)}")
    
    async def _send_custom_notification(self, custom_data: Dict) -> None:
        """Custom bildirim gönderme"""
        message = custom_data.get('message', 'Custom notification')
        
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(message)
    
    # Public methods for queuing notifications
    async def notify_trade(self, trade_data: Dict, priority: str = 'normal') -> None:
        """Trade bildirimi queue'ya ekleme"""
        await self.message_queue.put({
            'type': 'trade',
            'data': trade_data,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def notify_performance(self, performance_data: Dict, 
                               priority: str = 'normal') -> None:
        """Performans bildirimi queue'ya ekleme"""
        await self.message_queue.put({
            'type': 'performance',
            'data': performance_data,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def notify_risk(self, risk_data: Dict, priority: str = 'high') -> None:
        """Risk bildirimi queue'ya ekleme"""
        await self.message_queue.put({
            'type': 'risk',
            'data': risk_data,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def notify_signal(self, signal_data: Dict, priority: str = 'normal') -> None:
        """Sinyal bildirimi queue'ya ekleme"""
        await self.message_queue.put({
            'type': 'signal',
            'data': signal_data,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def notify_custom(self, message: str, priority: str = 'normal') -> None:
        """Custom bildirim queue'ya ekleme"""
        await self.message_queue.put({
            'type': 'custom',
            'data': {'message': message},
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def send_startup_notification(self) -> None:
        """Bot başlangıç bildirimi"""
        startup_message = """
🚀 <b>Smart Investment Bot Started</b>

✅ All systems initialized
📊 Ready for trading
🔔 Notifications active

⏰ Started: {time}
        """.strip().format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        await self.notify_custom(startup_message, priority='high')
    
    async def send_shutdown_notification(self, performance_summary: Dict = None) -> None:
        """Bot kapatma bildirimi"""
        if performance_summary:
            shutdown_message = f"""
🔴 <b>Smart Investment Bot Stopped</b>

📊 Final Performance:
💼 Portfolio Value: ${performance_summary.get('total_value', 0):.2f}
📈 Total Return: {performance_summary.get('total_return_pct', 0):+.2%}
🎯 Win Rate: {performance_summary.get('win_rate', 0):.1%}

⏰ Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        else:
            shutdown_message = f"""
🔴 <b>Smart Investment Bot Stopped</b>

⏰ Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
        
        await self.notify_custom(shutdown_message, priority='high')
    
    def get_notification_stats(self) -> Dict:
        """
        Bildirim istatistikleri
        
        Returns:
            Bildirim stats
        """
        return {
            'telegram_enabled': self.telegram_notifier is not None,
            'discord_enabled': self.discord_notifier is not None,
            'queue_size': self.message_queue.qsize(),
            'service_running': self.is_running
        }