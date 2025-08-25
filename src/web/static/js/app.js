/**
 * Smart Investment Bot Dashboard JavaScript
 * Real-time dashboard functionality
 */

class Dashboard {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.performanceChart = null;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.initializeChart();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Bot control buttons
        document.getElementById('startBtn').addEventListener('click', () => this.startBot());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopBot());
        document.getElementById('emergencyBtn').addEventListener('click', () => this.emergencyStop());
        
        // Trading form
        document.getElementById('tradingForm').addEventListener('submit', (e) => this.handleTradeSubmit(e));
        
        // Refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.onclick && e.target.onclick.toString().includes('refreshOpportunities')) {
                this.refreshOpportunities();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 't':
                        e.preventDefault();
                        this.openTradingModal();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshData();
                        break;
                }
            }
        });
    }
    
    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showToast('WebSocket connection error', 'error');
            };
            
        } catch (error) {
            console.error('Error connecting WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            console.log(`Attempting to reconnect in ${delay/1000} seconds (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            this.showToast('Failed to establish WebSocket connection', 'error');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'real_time_update':
                this.updateRealTimeData(data);
                break;
            case 'trade_executed':
                this.handleTradeUpdate(data);
                break;
            case 'alert':
                this.handleAlert(data);
                break;
            case 'emergency_stop':
                this.handleEmergencyStop(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateRealTimeData(data) {
        // Update bot status
        this.updateBotStatus(data.bot_status);
        
        // Update portfolio metrics
        this.updatePortfolioMetrics(data.portfolio);
        
        // Update performance
        this.updatePerformanceMetrics(data.performance);
        
        // Update last updated time
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
    }
    
    updateBotStatus(status) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (status.is_running) {
            statusIndicator.classList.add('running');
            statusText.textContent = 'Running';
            statusText.className = 'status-running';
        } else {
            statusIndicator.classList.remove('running');
            statusText.textContent = 'Stopped';
            statusText.className = 'status-stopped';
        }
        
        // Update trading status
        const tradingStatus = status.is_trading_enabled ? 'Enabled' : 'Disabled';
        // You can add a trading status indicator here
    }
    
    updatePortfolioMetrics(portfolio) {
        // Update portfolio values
        document.getElementById('totalValue').textContent = 
            this.formatCurrency(portfolio.total_value);
        
        const totalReturnEl = document.getElementById('totalReturn');
        const totalReturnPct = portfolio.total_return_percentage || 0;
        totalReturnEl.textContent = this.formatPercentage(totalReturnPct);
        totalReturnEl.className = `metric-value ${totalReturnPct >= 0 ? 'positive' : 'negative'}`;
        
        document.getElementById('cashBalance').textContent = 
            this.formatCurrency(portfolio.cash_balance || 0);
        
        // Update positions count
        document.getElementById('positionsCount').textContent = 
            portfolio.active_positions || 0;
    }
    
    updatePerformanceMetrics(performance) {
        const dailyReturnEl = document.getElementById('dailyReturn');
        const dailyReturn = performance.daily_return || 0;
        dailyReturnEl.textContent = this.formatPercentage(dailyReturn);
        dailyReturnEl.className = `metric-value ${dailyReturn >= 0 ? 'positive' : 'negative'}`;
        
        // Update trading statistics
        const tradingStats = performance.trade_statistics || {};
        document.getElementById('totalTrades').textContent = tradingStats.total_trades || 0;
        document.getElementById('winRate').textContent = 
            this.formatPercentage(tradingStats.win_rate || 0);
    }
    
    async loadInitialData() {
        try {
            this.showLoading(true);
            
            // Load portfolio data
            await this.loadPortfolioData();
            
            // Load recent trades
            await this.loadRecentTrades();
            
            // Load opportunities
            await this.loadOpportunities();
            
            // Load alerts
            await this.loadAlerts();
            
            this.showLoading(false);
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading dashboard data', 'error');
            this.showLoading(false);
        }
    }
    
    async loadPortfolioData() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update active positions table
            this.updatePositionsTable(data.active_positions || []);
            
        } catch (error) {
            console.error('Error loading portfolio:', error);
        }
    }
    
    async loadRecentTrades() {
        try {
            const response = await fetch('/api/trades?limit=10');
            const data = await response.json();
            
            this.updateTradesTable(data.trades || []);
            
        } catch (error) {
            console.error('Error loading trades:', error);
        }
    }
    
    async loadOpportunities() {
        try {
            const response = await fetch('/api/opportunities');
            const data = await response.json();
            
            this.updateOpportunitiesDisplay(data.opportunities || []);
            
        } catch (error) {
            console.error('Error loading opportunities:', error);
        }
    }
    
    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();
            
            this.updateAlertsDisplay(data.alerts || []);
            
        } catch (error) {
            console.error('Error loading alerts:', error);
        }
    }
    
    updatePositionsTable(positions) {
        const tbody = document.getElementById('positionsTableBody');
        
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-data">No active positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(position => `
            <tr>
                <td><strong>${position.symbol}</strong></td>
                <td><span class="badge">${position.asset_type}</span></td>
                <td>${this.formatNumber(position.amount)}</td>
                <td>${this.formatCurrency(position.current_price)}</td>
                <td>${this.formatCurrency(position.market_value)}</td>
                <td class="${position.unrealized_pnl >= 0 ? 'price-up' : 'price-down'}">
                    ${this.formatCurrency(position.unrealized_pnl)}
                </td>
                <td class="${position.unrealized_pnl_pct >= 0 ? 'price-up' : 'price-down'}">
                    ${this.formatPercentage(position.unrealized_pnl_pct)}
                </td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="dashboard.sellPosition('${position.symbol}')">
                        Sell
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    updateTradesTable(trades) {
        const tbody = document.getElementById('tradesTableBody');
        
        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No recent trades</td></tr>';
            return;
        }
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${new Date(trade.created_at).toLocaleTimeString()}</td>
                <td>
                    <span class="badge ${trade.trade_type === 'BUY' ? 'success' : 'danger'}">
                        ${trade.trade_type}
                    </span>
                </td>
                <td><strong>${trade.symbol}</strong></td>
                <td>${this.formatNumber(trade.amount)}</td>
                <td>${this.formatCurrency(trade.price)}</td>
                <td class="${trade.profit_loss >= 0 ? 'price-up' : 'price-down'}">
                    ${this.formatCurrency(trade.profit_loss)}
                </td>
                <td><span class="badge">${trade.strategy || 'manual'}</span></td>
            </tr>
        `).join('');
        
        document.getElementById('tradesCount').textContent = trades.length;
    }
    
    updateOpportunitiesDisplay(opportunities) {
        const container = document.getElementById('opportunitiesList');
        
        if (opportunities.length === 0) {
            container.innerHTML = '<p class="no-data">No opportunities detected</p>';
            return;
        }
        
        container.innerHTML = opportunities.map(opp => `
            <div class="opportunity-item" onclick="dashboard.tradeOpportunity('${opp.symbol}', '${opp.action}')">
                <div class="opportunity-header">
                    <span class="opportunity-symbol">${opp.symbol}</span>
                    <span class="opportunity-confidence">${this.formatPercentage(opp.confidence)} confidence</span>
                </div>
                <div class="opportunity-details">
                    <strong>${opp.action}</strong> - ${opp.reason}
                    <br>Target: ${this.formatCurrency(opp.target_price)}
                </div>
            </div>
        `).join('');
    }
    
    updateAlertsDisplay(alerts) {
        const alertsList = document.getElementById('alertsList');
        
        if (alerts.length === 0) {
            alertsList.innerHTML = '<p class="no-data">No alerts</p>';
            return;
        }
        
        alertsList.innerHTML = alerts.map(alert => `
            <div class="alert-item ${alert.severity}" onclick="dashboard.markAlertRead(${alert.id})">
                <div class="alert-time">${new Date(alert.created_at).toLocaleString()}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        `).join('');
        
        // Show alerts panel if there are unread alerts
        if (alerts.length > 0) {
            this.showAlertsPanel();
        }
    }
    
    initializeChart() {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Total Return %',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: 'rgba(203, 213, 225, 0.1)'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {
                            color: '#cbd5e1',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(203, 213, 225, 0.1)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            color: '#cbd5e1',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }
    
    async updateChart(days = 30) {
        try {
            const response = await fetch(`/api/performance/${days}`);
            const data = await response.json();
            
            if (data.performance) {
                const labels = data.performance.map(p => 
                    new Date(p.date).toLocaleDateString()
                ).reverse();
                
                const portfolioValues = data.performance.map(p => p.total_value).reverse();
                const returnPercentages = data.performance.map(p => p.total_return_pct * 100).reverse();
                
                this.performanceChart.data.labels = labels;
                this.performanceChart.data.datasets[0].data = portfolioValues;
                this.performanceChart.data.datasets[1].data = returnPercentages;
                
                this.performanceChart.update();
                
                // Update active button
                document.querySelectorAll('.chart-controls .btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
            }
            
        } catch (error) {
            console.error('Error updating chart:', error);
            this.showToast('Error updating chart', 'error');
        }
    }
    
    async startBot() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/bot/start', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Bot started successfully', 'success');
            } else {
                this.showToast(result.message || 'Failed to start bot', 'error');
            }
            
        } catch (error) {
            console.error('Error starting bot:', error);
            this.showToast('Error starting bot', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async stopBot() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/bot/stop', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Bot stopped successfully', 'success');
            } else {
                this.showToast(result.message || 'Failed to stop bot', 'error');
            }
            
        } catch (error) {
            console.error('Error stopping bot:', error);
            this.showToast('Error stopping bot', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async emergencyStop() {
        if (!confirm('Are you sure you want to execute emergency stop? This will close all positions.')) {
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/emergency-stop', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Emergency stop executed', 'warning');
                this.refreshData();
            } else {
                this.showToast(result.error || 'Emergency stop failed', 'error');
            }
            
        } catch (error) {
            console.error('Error executing emergency stop:', error);
            this.showToast('Emergency stop error', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleTradeSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const tradeRequest = {
            symbol: document.getElementById('tradeSymbol').value,
            action: document.getElementById('tradeAction').value,
            amount: parseFloat(document.getElementById('tradeAmount').value),
            price: document.getElementById('tradePrice').value ? 
                   parseFloat(document.getElementById('tradePrice').value) : null
        };
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/trade/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(tradeRequest)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Trade executed successfully', 'success');
                this.closeTradingModal();
                this.refreshData();
            } else {
                this.showToast(result.error || 'Trade execution failed', 'error');
            }
            
        } catch (error) {
            console.error('Error executing trade:', error);
            this.showToast('Trade execution error', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async refreshOpportunities() {
        try {
            const response = await fetch('/api/opportunities');
            const data = await response.json();
            
            this.updateOpportunitiesDisplay(data.opportunities || []);
            this.showToast('Opportunities refreshed', 'info');
            
        } catch (error) {
            console.error('Error refreshing opportunities:', error);
            this.showToast('Error refreshing opportunities', 'error');
        }
    }
    
    async sellPosition(symbol) {
        if (!confirm(`Are you sure you want to sell all ${symbol}?`)) {
            return;
        }
        
        // Get current position amount
        const positions = await this.getCurrentPositions();
        const position = positions.find(p => p.symbol === symbol);
        
        if (!position) {
            this.showToast('Position not found', 'error');
            return;
        }
        
        const tradeRequest = {
            symbol: symbol,
            action: 'SELL',
            amount: position.amount
        };
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/trade/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(tradeRequest)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast(`Sold ${symbol} successfully`, 'success');
                this.refreshData();
            } else {
                this.showToast(result.error || 'Sell order failed', 'error');
            }
            
        } catch (error) {
            console.error('Error selling position:', error);
            this.showToast('Sell order error', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async getCurrentPositions() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();
            return data.active_positions || [];
        } catch (error) {
            console.error('Error getting current positions:', error);
            return [];
        }
    }
    
    tradeOpportunity(symbol, action) {
        // Pre-fill trading modal with opportunity data
        document.getElementById('tradeSymbol').value = symbol;
        document.getElementById('tradeAction').value = action;
        
        this.openTradingModal();
    }
    
    async markAlertRead(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/read`, { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                // Remove alert from display
                event.target.closest('.alert-item').remove();
            }
            
        } catch (error) {
            console.error('Error marking alert as read:', error);
        }
    }
    
    // UI Helper Methods
    openTradingModal() {
        document.getElementById('tradingModal').classList.add('open');
    }
    
    closeTradingModal() {
        document.getElementById('tradingModal').classList.remove('open');
        document.getElementById('tradingForm').reset();
    }
    
    showAlertsPanel() {
        document.getElementById('alertsPanel').classList.add('open');
    }
    
    closeAlerts() {
        document.getElementById('alertsPanel').classList.remove('open');
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        container.removeChild(toast);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    updateConnectionStatus(connected) {
        const statusText = document.getElementById('statusText');
        if (!connected) {
            statusText.textContent = 'Disconnected';
            statusText.className = 'status-warning';
        }
        // Will be updated by real-time data when connected
    }
    
    async refreshData() {
        await this.loadInitialData();
        this.showToast('Data refreshed', 'info');
    }
    
    // Formatting Helpers
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value || 0);
    }
    
    formatPercentage(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format((value || 0) / 100);
    }
    
    formatNumber(value, decimals = 4) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimals
        }).format(value || 0);
    }
}

// Global functions for onclick handlers
window.updateChart = function(days) {
    dashboard.updateChart(days);
};

window.refreshOpportunities = function() {
    dashboard.refreshOpportunities();
};

window.closeAlerts = function() {
    dashboard.closeAlerts();
};

window.closeTradingModal = function() {
    dashboard.closeTradingModal();
};

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && dashboard) {
        // Refresh data when page becomes visible
        dashboard.refreshData();
    }
});