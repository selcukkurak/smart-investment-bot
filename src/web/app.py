"""
FastAPI Web Application - Web dashboard
Real-time bot monitoring ve control dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

# Import bot components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bot import SmartInvestmentBot
from utils.config import ConfigManager
from utils.logger import get_logger
from database.database import DatabaseManager


class WebSocketManager:
    """WebSocket bağlantı yönetimi"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global instances
app = FastAPI(title="Smart Investment Bot Dashboard", version="1.0.0")
websocket_manager = WebSocketManager()
config_manager = ConfigManager()
db_manager = DatabaseManager()
bot_instance = None
logger = get_logger('WebApp')

# Static files and templates
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    global bot_instance
    
    try:
        # Load configuration
        await config_manager.load_config()
        
        # Initialize database
        await db_manager.initialize()
        
        # Initialize bot
        initial_capital = config_manager.get('bot.initial_capital', 10000.0)
        bot_instance = SmartInvestmentBot(initial_capital)
        await bot_instance.initialize()
        
        # Start real-time data broadcasting
        asyncio.create_task(broadcast_real_time_data())
        
        logger.info("🚀 Web application started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """FastAPI shutdown event"""
    global bot_instance
    
    try:
        if bot_instance:
            await bot_instance.stop()
        
        await db_manager.close()
        
        logger.info("🔴 Web application shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")


# Web routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Ana dashboard sayfası"""
    try:
        # Bot status
        bot_status = bot_instance.get_bot_status() if bot_instance else {
            'is_running': False,
            'portfolio': {'total_value': 0, 'total_return_percentage': 0}
        }
        
        # Recent performance
        performance_history = await db_manager.get_performance_history(7)
        
        # Active positions
        positions = await db_manager.get_portfolio_positions()
        
        # Recent trades
        recent_trades = await db_manager.get_trades(limit=10)
        
        # Trading statistics
        trading_stats = await db_manager.get_trading_statistics(30)
        
        dashboard_data = {
            'bot_status': bot_status,
            'performance_history': performance_history,
            'active_positions': positions,
            'recent_trades': recent_trades,
            'trading_stats': trading_stats,
            'last_updated': datetime.now().isoformat()
        }
        
        return templates.TemplateResponse(
            "dashboard.html", 
            {"request": request, "data": dashboard_data}
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Dashboard load error")


# API endpoints
@app.get("/api/status")
async def get_bot_status():
    """Bot durumu API"""
    if bot_instance:
        return bot_instance.get_bot_status()
    else:
        return {"error": "Bot not initialized"}


@app.post("/api/bot/start")
async def start_bot():
    """Bot başlatma API"""
    if bot_instance and not bot_instance.is_running:
        asyncio.create_task(bot_instance.start())
        return {"success": True, "message": "Bot started"}
    else:
        return {"success": False, "message": "Bot already running or not initialized"}


@app.post("/api/bot/stop")
async def stop_bot():
    """Bot durdurma API"""
    if bot_instance and bot_instance.is_running:
        await bot_instance.stop()
        return {"success": True, "message": "Bot stopped"}
    else:
        return {"success": False, "message": "Bot not running"}


@app.post("/api/bot/enable-trading")
async def enable_trading():
    """Trading aktifleştirme API"""
    if bot_instance:
        bot_instance.enable_trading()
        return {"success": True, "message": "Trading enabled"}
    else:
        return {"error": "Bot not initialized"}


@app.post("/api/bot/disable-trading")
async def disable_trading():
    """Trading deaktifleştirme API"""
    if bot_instance:
        bot_instance.disable_trading()
        return {"success": True, "message": "Trading disabled"}
    else:
        return {"error": "Bot not initialized"}


@app.get("/api/portfolio")
async def get_portfolio():
    """Portfolio bilgileri API"""
    try:
        if bot_instance:
            portfolio_summary = bot_instance.portfolio_manager.get_portfolio_summary()
            return portfolio_summary
        else:
            return {"error": "Bot not initialized"}
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail="Portfolio data error")


@app.get("/api/trades")
async def get_trades(symbol: str = None, limit: int = 50):
    """Trade geçmişi API"""
    try:
        trades = await db_manager.get_trades(symbol=symbol, limit=limit)
        return {"trades": trades}
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail="Trades data error")


@app.get("/api/performance/{days}")
async def get_performance_history(days: int):
    """Performans geçmişi API"""
    try:
        performance = await db_manager.get_performance_history(days)
        return {"performance": performance}
    except Exception as e:
        logger.error(f"Error getting performance history: {str(e)}")
        raise HTTPException(status_code=500, detail="Performance data error")


@app.post("/api/trade/execute")
async def execute_manual_trade(trade_request: Dict):
    """Manuel trade çalıştırma API"""
    try:
        if not bot_instance:
            return {"success": False, "error": "Bot not initialized"}
        
        result = await bot_instance.execute_trade(
            symbol=trade_request['symbol'],
            action=trade_request['action'],
            amount=trade_request['amount'],
            price=trade_request.get('price'),
            strategy='manual'
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing manual trade: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/opportunities")
async def get_market_opportunities():
    """Piyasa fırsatları API"""
    try:
        if bot_instance:
            opportunities = await bot_instance.get_market_opportunities()
            return {"opportunities": opportunities}
        else:
            return {"opportunities": []}
    except Exception as e:
        logger.error(f"Error getting opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail="Opportunities data error")


@app.get("/api/alerts")
async def get_alerts():
    """Uyarılar API"""
    try:
        alerts = await db_manager.get_unread_alerts(50)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Alerts data error")


@app.post("/api/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    """Uyarıyı okundu işaretleme API"""
    try:
        success = await db_manager.mark_alert_read(alert_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error marking alert as read: {str(e)}")
        return {"success": False, "error": str(e)}


@app.get("/api/config")
async def get_configuration():
    """Konfigürasyon API"""
    try:
        # Sensitive bilgileri çıkar
        config = config_manager.get_all_config()
        
        # Remove API keys and secrets
        if 'apis' in config:
            for api_name, api_config in config['apis'].items():
                if 'api_key' in api_config:
                    api_config['api_key'] = '***hidden***'
                if 'api_secret' in api_config:
                    api_config['api_secret'] = '***hidden***'
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Configuration error")


@app.post("/api/config/update")
async def update_configuration(config_update: Dict):
    """Konfigürasyon güncelleme API"""
    try:
        success = True
        updated_keys = []
        
        for key_path, value in config_update.items():
            if config_manager.set(key_path, value):
                updated_keys.append(key_path)
            else:
                success = False
        
        if success:
            await config_manager.save_config()
        
        return {
            "success": success,
            "updated_keys": updated_keys,
            "message": f"Updated {len(updated_keys)} configuration keys"
        }
        
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return {"success": False, "error": str(e)}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time veri WebSocket endpoint"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back or handle client messages
            if data:
                response = {"type": "pong", "timestamp": datetime.now().isoformat()}
                await websocket_manager.send_personal_message(response, websocket)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)


async def broadcast_real_time_data():
    """Real-time veri broadcasting"""
    while True:
        try:
            if bot_instance and websocket_manager.active_connections:
                # Bot status
                bot_status = bot_instance.get_bot_status()
                
                # Portfolio summary
                portfolio_summary = bot_instance.portfolio_manager.get_portfolio_summary()
                
                # Performance metrics
                performance = bot_instance.portfolio_manager.get_performance_metrics()
                
                # Real-time data package
                real_time_data = {
                    "type": "real_time_update",
                    "timestamp": datetime.now().isoformat(),
                    "bot_status": bot_status,
                    "portfolio": portfolio_summary,
                    "performance": performance
                }
                
                # Broadcast to all connected clients
                await websocket_manager.broadcast(real_time_data)
            
            # Update every 10 seconds
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in real-time broadcasting: {str(e)}")
            await asyncio.sleep(30)  # Wait longer on error


# Additional utility endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check bot status
        bot_healthy = bot_instance is not None
        
        # Check database
        db_stats = await db_manager.get_database_stats()
        db_healthy = bool(db_stats)
        
        # Check configuration
        config_healthy = bool(config_manager.config_data)
        
        overall_health = bot_healthy and db_healthy and config_healthy
        
        return {
            "healthy": overall_health,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "bot": bot_healthy,
                "database": db_healthy,
                "configuration": config_healthy
            },
            "database_stats": db_stats
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/statistics")
async def get_statistics():
    """Genel istatistikler API"""
    try:
        # Trading statistics
        trading_stats = await db_manager.get_trading_statistics(30)
        
        # Database statistics
        db_stats = await db_manager.get_database_stats()
        
        # Bot performance
        performance_history = await db_manager.get_performance_history(30)
        
        return {
            "trading_statistics": trading_stats,
            "database_statistics": db_stats,
            "performance_summary": {
                "total_records": len(performance_history),
                "date_range": {
                    "start": performance_history[-1]['date'] if performance_history else None,
                    "end": performance_history[0]['date'] if performance_history else None
                }
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Statistics error")


@app.post("/api/emergency-stop")
async def emergency_stop():
    """Acil durum durdurma API"""
    try:
        if bot_instance:
            result = await bot_instance.emergency_stop()
            
            # Alert broadcast
            await websocket_manager.broadcast({
                "type": "emergency_stop",
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return result
        else:
            return {"success": False, "error": "Bot not initialized"}
            
    except Exception as e:
        logger.error(f"Emergency stop error: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    # Load web configuration
    web_config = config_manager.get('web', {
        'host': '0.0.0.0',
        'port': 8000,
        'reload': False
    })
    
    uvicorn.run(
        "app:app",
        host=web_config['host'],
        port=web_config['port'],
        reload=web_config['reload'],
        log_level="info"
    )