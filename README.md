# Python Trading Bot

## Description
This repository contains a Python-based trading bot designed to help users automate and manage their investment portfolios. The bot integrates with the TD Ameritrade API for secure trade execution and account management. It features modular architecture for market data handling, portfolio management, and technical indicator analysis.

## Features
- **Automated Trading**: A modular class-based system for managing trading sessions, detecting market states (pre-market, post-market, and regular trading hours), and executing trade orders.
- **Technical Analysis**: Implements indicators such as RSI, SMA, and EMA, along with a custom price change tracker. Allows for dynamic refresh of calculated indicators.
- **Signal Evaluation**: Configurable buy/sell conditions using indicator thresholds and logical operators like greater-than or less-than.
- **Portfolio Management**: Enables adding, removing, and analyzing positions within a portfolio. Supports profit/loss tracking and allocation management across asset types.
- **Data Handling**: Provides a multi-indexed `StockFrame` for managing real-time and historical market data grouped by asset symbol and timestamp.
- **Secure API Integration**: Uses TD Ameritrade's API for placing orders, retrieving account details, and accessing market data.

## Modules
1. **indicators.py**: Manages technical indicators and signals for trading decisions.
2. **order_status.py**: Tracks the status of trade orders (e.g., filled, canceled, or pending).
3. **portfolio.py**: Handles portfolio operations, including position tracking, risk evaluation, and market value calculations.
4. **robot.py**: The main bot interface for managing sessions, portfolios, and executing trades.
5. **stock_frame.py**: Provides a structured DataFrame for organizing market data and calculating indicators.
6. **trades.py**: Facilitates trade creation, order customization, and execution management.

## Technologies
- Python 3
- pandas & NumPy
- TD Ameritrade API (via `td.client`)
- Object-Oriented Programming (OOP)

## Usage
1. Clone the repository: `git clone https://github.com/tommynguyenn53/python-trading-bot.git`
2. Install required dependencies: `pip install -r requirements.txt`
3. Configure your TD Ameritrade API credentials in `robot.py`.
4. Run the trading bot: `python robot.py`

