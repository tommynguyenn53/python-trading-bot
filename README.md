# Python Trading Bot

## Description
This is a Python-based Trading Bot designed to help users automate and manage their investment portfolio. The system allows for real-time market data handling, trade execution strategy configuration, and technical indicator analysis. Users can track asset performance, evaluate signals like RSI, SMA, and EMA, and configure trades programmatically.

## Features
- 🔁 Automated Trading Architecture: Modular class-based design for trade session handling, market state detection, and trade order creation
- 📈 Technical Indicators: Support for RSI, SMA, EMA, and custom price change tracking with dynamic refresh capability
- 🧠 Signal Evaluation: Configurable buy/sell conditions based on indicator thresholds and logical operators
- 📊 Market Data Management: Real-time price frame management via multi-indexed DataFrames grouped by asset symbol and timestamp
- 🔒 TD Ameritrade Integration: Secure session management using TDClient for order placement and account interaction

## Technologies
- Python 3
- pandas & NumPy
- TD Ameritrade API (via td.client)
- Object-Oriented Programming (OOP)