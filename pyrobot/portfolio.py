import numpy as np

from pandas import DataFrame
from typing import Tuple
from typing import List
from typing import Optional


from pyrobot.stock_frame import StockFrame
from td.client import TDClient


class Portfolio():

    def __init__(self, account_number: Optional[str] = None) -> None:


        self.positions = {}
        self.positions_count = 0

        self.profit_loss = 0.00
        self.market_value = 0.00
        self.risk_tolerance = 0.00
        self.account_number = account_number

        self._historical_prices = []

        self._td_client: TDClient = None
        self._stock_frame: StockFrame = None
        self._stock_frame_daily: StockFrame = None

    def add_positions(self, positions: List[dict]) -> dict:


        if isinstance(positions, list):

            # Loop through each position.
            for position in positions:

                # Add the position.
                self.add_position(
                    symbol=position['symbol'],
                    asset_type=position['asset_type'],
                    quantity=position.get('quantity', 0),
                    purchase_price=position.get('purchase_price', 0.0),
                    purchase_date=position.get('purchase_date', None)
                )

            return self.positions

        else:
            raise TypeError('Positions must be a list of dictionaries.')

    def add_position(self, symbol: str, asset_type: str, purchase_date: Optional[str] = None, quantity: int = 0, purchase_price: float = 0.0) -> dict:


        self.positions[symbol] = {}
        self.positions[symbol]['symbol'] = symbol
        self.positions[symbol]['quantity'] = quantity
        self.positions[symbol]['purchase_price'] = purchase_price
        self.positions[symbol]['purchase_date'] = purchase_date
        self.positions[symbol]['asset_type'] = asset_type

        if purchase_date:
            self.positions[symbol]['ownership_status'] = True
        else:
            self.positions[symbol]['ownership_status'] = False

        return self.positions[symbol]

    def remove_position(self, symbol: str) -> Tuple[bool, str]:

        if symbol in self.positions:
            del self.positions[symbol]
            return (True, "{symbol} was successfully removed.".format(symbol=symbol))
        else:
            return (False, "{symbol} did not exist in the porfolio.".format(symbol=symbol))

    def total_allocation(self) -> dict:

        total_allocation = {
            'stocks': [],
            'fixed_income': [],
            'options': [],
            'futures': [],
            'furex': []
        }

        if len(self.positions.keys()) > 0:
            for symbol in self.positions:
                total_allocation[self.positions[symbol]['asset_type']].append(self.positions[symbol])

    def portfolio_variance(self, weights: dict, covariance_matrix: DataFrame) -> dict:

        sorted_keys = list(weights.keys())
        sorted_keys.sort()

        sorted_weights = np.array([weights[symbol] for symbol in sorted_keys])
        portfolio_variance = np.dot(
            sorted_weights.T,
            np.dot(covariance_matrix, sorted_weights)
        )

        return portfolio_variance

    def portfolio_metrics(self) -> dict:


        if not self._stock_frame_daily:
            self._grab_daily_historical_prices()

        # Calculate the weights.
        porftolio_weights = self.portfolio_weights()

        # Calculate the Daily Returns (%)
        self._stock_frame_daily.frame['daily_returns_pct'] = self._stock_frame_daily.symbol_groups['close'].transform(
            lambda x: x.pct_change()
        )

        # Calculate the Daily Returns (Mean)
        self._stock_frame_daily.frame['daily_returns_avg'] = self._stock_frame_daily.symbol_groups['daily_returns_pct'].transform(
            lambda x: x.mean()
        )

        # Calculate the Daily Returns (Standard Deviation)
        self._stock_frame_daily.frame['daily_returns_std'] = self._stock_frame_daily.symbol_groups['daily_returns_pct'].transform(
            lambda x: x.std()
        )

        # Calculate the Covariance.
        returns_cov = self._stock_frame_daily.frame.unstack(
            level=0)['daily_returns_pct'].cov()

        # Take the other columns and get ready to add them to our dictionary.
        returns_avg = self._stock_frame_daily.symbol_groups['daily_returns_avg'].tail(
            n=1
        ).to_dict()

        returns_std = self._stock_frame_daily.symbol_groups['daily_returns_std'].tail(
            n=1
        ).to_dict()

        metrics_dict = {}

        portfolio_variance = self.portfolio_variance(
            weights=porftolio_weights,
            covariance_matrix=returns_cov
        )

        for index_tuple in returns_std:

            symbol = index_tuple[0]
            metrics_dict[symbol] = {}
            metrics_dict[symbol]['weight'] = porftolio_weights[symbol]
            metrics_dict[symbol]['average_returns'] = returns_avg[index_tuple]
            metrics_dict[symbol]['weighted_returns'] = returns_avg[index_tuple] * \
                metrics_dict[symbol]['weight']
            metrics_dict[symbol]['standard_deviation_of_returns'] = returns_std[index_tuple]
            metrics_dict[symbol]['variance_of_returns'] = returns_std[index_tuple] ** 2
            metrics_dict[symbol]['covariance_of_returns'] = returns_cov.loc[[
                symbol]].to_dict()

        metrics_dict['portfolio'] = {}
        metrics_dict['portfolio']['variance'] = portfolio_variance

        return metrics_dict

    def portfolio_weights(self) -> dict:

        weights = {}

        # First grab all the symbols.
        symbols = self.positions.keys()

        # Grab the quotes.
        quotes = self.td_client.get_quotes(instruments=list(symbols))

        # Grab the projected market value.
        projected_market_value_dict = self.projected_market_value(
            current_prices=quotes
        )

        # Loop through each symbol.
        for symbol in projected_market_value_dict:

            # Calculate the weights.
            if symbol != 'total':
                weights[symbol] = projected_market_value_dict[symbol]['total_market_value'] / \
                    projected_market_value_dict['total']['total_market_value']

        return weights

    def portfolio_summary(self):

        # First grab all the symbols.
        symbols = self.positions.keys()

        # Grab the quotes.
        quotes = self.td_client.get_quotes(instruments=list(symbols))

        portfolio_summary_dict = {}
        portfolio_summary_dict['projected_market_value'] = self.projected_market_value(
            current_prices=quotes
        )
        portfolio_summary_dict['portfolio_weights'] = self.portfolio_weights()
        portfolio_summary_dict['portfolio_risk'] = ""

        return portfolio_summary_dict

    def in_portfolio(self, symbol: str) -> bool:


        if symbol in self.positions:
            return True
        else:
            return False

    def get_ownership_status(self, symbol: str) -> bool:


        if self.in_portfolio(symbol=symbol) and self.positions[symbol]['ownership_status']:
            return self.positions[symbol]['ownership_status']
        else:
            return False

    def set_ownership_status(self, symbol: str, ownership: bool) -> None:


        if self.in_portfolio(symbol=symbol):
            self.positions[symbol]['ownership_status'] = ownership
        else:
            raise KeyError(
                "Can't set ownership status, as you do not have the symbol in your portfolio."
            )

    def is_profitable(self, symbol: str, current_price: float) -> bool:


        # Grab the purchase price, if it exists.
        if self.in_portfolio(symbol=symbol):
            purchase_price = self.positions[symbol]['purchase_price']
        else:
            raise KeyError("The Symbol you tried to request does not exist.")

        if (purchase_price <= current_price):
            return True
        elif (purchase_price > current_price):
            return False

    def projected_market_value(self, current_prices: dict) -> dict:


        projected_value = {}
        total_value = 0.0
        total_invested_capital = 0.0
        total_profit_or_loss = 0.0

        position_count_profitable = 0
        position_count_not_profitable = 0
        position_count_break_even = 0

        for symbol in current_prices:

            if self.in_portfolio(symbol=symbol):

                projected_value[symbol] = {}
                current_quantity = self.positions[symbol]['quantity']
                purchase_price = self.positions[symbol]['purchase_price']
                current_price = current_prices[symbol]['lastPrice']
                is_profitable = self.is_profitable(
                    symbol=symbol, current_price=current_price)

                projected_value[symbol]['purchase_price'] = purchase_price
                projected_value[symbol]['current_price'] = current_prices[symbol]['lastPrice']
                projected_value[symbol]['quantity'] = current_quantity
                projected_value[symbol]['is_profitable'] = is_profitable

                # Calculate total market value.
                projected_value[symbol]['total_market_value'] = (
                    current_price * current_quantity
                )

                # Calculate total invested capital.
                projected_value[symbol]['total_invested_capital'] = (
                    current_quantity * purchase_price
                )

                projected_value[symbol]['total_loss_or_gain_$'] = ((current_price - purchase_price) * current_quantity)
                projected_value[symbol]['total_loss_or_gain_%'] = round(((current_price - purchase_price) / purchase_price), 4)

                total_value += projected_value[symbol]['total_market_value']
                total_profit_or_loss += projected_value[symbol]['total_loss_or_gain_$']
                total_invested_capital += projected_value[symbol]['total_invested_capital']

                if projected_value[symbol]['total_loss_or_gain_$'] > 0:
                    position_count_profitable += 1
                elif projected_value[symbol]['total_loss_or_gain_$'] < 0:
                    position_count_not_profitable += 1
                else:
                    position_count_break_even += 1

        projected_value['total'] = {}
        projected_value['total']['total_positions'] = len(self.positions)
        projected_value['total']['total_market_value'] = total_value
        projected_value['total']['total_invested_capital'] = total_invested_capital
        projected_value['total']['total_profit_or_loss'] = total_profit_or_loss
        projected_value['total']['number_of_profitable_positions'] = position_count_profitable
        projected_value['total']['number_of_non_profitable_positions'] = position_count_not_profitable
        projected_value['total']['number_of_breakeven_positions'] = position_count_break_even

        return projected_value

    @property
    def historical_prices(self) -> List[dict]:


        return self._historical_prices

    @historical_prices.setter
    def historical_prices(self, historical_prices: List[dict]) -> None:


        self._historical_prices = historical_prices

    @property
    def stock_frame(self) -> StockFrame:


        return self._stock_frame

    @stock_frame.setter
    def stock_frame(self, stock_frame: StockFrame) -> None:

        self._stock_frame = stock_frame

    @property
    def td_client(self) -> TDClient:

        return self._td_client

    @td_client.setter
    def td_client(self, td_client: TDClient) -> None:

        self._td_client: TDClient = td_client

    def _grab_daily_historical_prices(self) -> StockFrame:

        new_prices = []

        # Loop through each position.
        for symbol in self.positions:

            # Grab the historical prices.
            historical_prices_response = self.td_client.get_price_history(
                symbol=symbol,
                period_type='year',
                period=1,
                frequency_type='daily',
                frequency=1,
                extended_hours=True
            )

            # Loop through the chandles.
            for candle in historical_prices_response['candles']:

                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                new_prices.append(new_price_mini_dict)

        # Create and set the StockFrame
        self._stock_frame_daily = StockFrame(data=new_prices)
        self._stock_frame_daily.create_frame()

        return self._stock_frame_daily