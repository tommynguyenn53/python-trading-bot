import json
import time as time_true
import pathlib
import pandas as pd

from datetime import datetime
from datetime import timezone
from datetime import timedelta

from typing import List
from typing import Dict
from typing import Union

from pyrobot.trades import Trade
from pyrobot.portfolio import Portfolio
from pyrobot.stock_frame import StockFrame

from td.client import TDClient
from td.utils import TDUtilities

milliseconds_since_epoch = TDUtilities().milliseconds_since_epoch


class PyRobot():

    def __init__(self, client_id: str, redirect_uri: str, paper_trading: bool = True, credentials_path: str = None,
                 trading_account: str = None) -> None:


        self.trading_account = trading_account
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.credentials_path = credentials_path
        self.session: TDClient = self._create_session()
        self.trades = {}
        self.historical_prices = {}
        self.stock_frame: StockFrame = None
        self.paper_trading = paper_trading

        self._bar_size = None
        self._bar_type = None

    def _create_session(self) -> TDClient:


        td_client = TDClient(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            credentials_path=self.credentials_path
        )

        # log the client into the new session
        td_client.login()

        return td_client

    @property
    def pre_market_open(self) -> bool:


        pre_market_start_time = datetime.utcnow().replace(
            hour=8,
            minute=00,
            second=00
        ).timestamp()

        market_start_time = datetime.utcnow().replace(
            hour=13,
            minute=30,
            second=00
        ).timestamp()

        right_now = datetime.utcnow().timestamp()

        if market_start_time >= right_now >= pre_market_start_time:
            return True
        else:
            return False

    @property
    def post_market_open(self):

        post_market_end_time = datetime.utcnow().replace(
            hour=00,
            minute=00,
            second=00
        ).timestamp()

        market_end_time = datetime.utcnow().replace(
            hour=20,
            minute=00,
            second=00
        ).timestamp()

        right_now = datetime.utcnow().timestamp()

        if post_market_end_time >= right_now >= market_end_time:
            return True
        else:
            return False

    @property
    def regular_market_open(self):


        market_start_time = datetime.utcnow().replace(
            hour=13,
            minute=30,
            second=00
        ).timestamp()

        market_end_time = datetime.utcnow().replace(
            hour=20,
            minute=00,
            second=00
        ).timestamp()

        right_now = datetime.utcnow().timestamp()

        if market_end_time >= right_now >= market_start_time:
            return True
        else:
            return False

    def create_portfolio(self) -> Portfolio:


        # Initalize the portfolio.
        self.portfolio = Portfolio(account_number=self.trading_account)

        # Assign the Client
        self.portfolio.td_client = self.session

        return self.portfolio

    def create_trade(self, trade_id: str, enter_or_exit: str, long_or_short: str, order_type: str = 'mkt',
                     price: float = 0.0, stop_limit_price=0.0) -> Trade:

        # Initalize a new trade object.
        trade = Trade()

        # Create a new trade.
        trade.new_trade(
            trade_id=trade_id,
            order_type=order_type,
            side=long_or_short,
            enter_or_exit=enter_or_exit,
            price=price,
            stop_limit_price=stop_limit_price
        )

        # Set the Client.
        trade.account = self.trading_account
        trade._td_client = self.session

        self.trades[trade_id] = trade

        return trade

    def delete_trade(self, index: int) -> None:


        if index in self.trades:
            del self.trades[index]

    def grab_current_quotes(self) -> dict:


        # First grab all the symbols.
        symbols = self.portfolio.positions.keys()

        # Grab the quotes.
        quotes = self.session.get_quotes(instruments=list(symbols))

        return quotes

    def grab_historical_prices(self, start: datetime, end: datetime, bar_size: int = 1,
                               bar_type: str = 'minute', symbols: List[str] = None) -> List[dict]:

        self._bar_size = bar_size
        self._bar_type = bar_type

        start = str(milliseconds_since_epoch(dt_object=start))
        end = str(milliseconds_since_epoch(dt_object=end))

        new_prices = []

        if not symbols:
            symbols = self.portfolio.positions

        for symbol in symbols:

            historical_prices_response = self.session.get_price_history(
                symbol=symbol,
                period_type='day',
                start_date=start,
                end_date=end,
                frequency_type=bar_type,
                frequency=bar_size,
                extended_hours=True
            )

            self.historical_prices[symbol] = {}
            self.historical_prices[symbol]['candles'] = historical_prices_response['candles']

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

        self.historical_prices['aggregated'] = new_prices

        return self.historical_prices

    def get_latest_bar(self) -> List[dict]:


        # Grab the info from the last quest.
        bar_size = self._bar_size
        bar_type = self._bar_type

        # Define the start and end date.
        end_date = datetime.today()
        start_date = end_date - timedelta(days=1)
        start = str(milliseconds_since_epoch(dt_object=start_date))
        end = str(milliseconds_since_epoch(dt_object=end_date))

        latest_prices = []

        # Loop through each symbol.
        for symbol in self.portfolio.positions:

            try:

                # Grab the request.
                historical_prices_response = self.session.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            except:

                time_true.sleep(2)

                # Grab the request.
                historical_prices_response = self.session.get_price_history(
                    symbol=symbol,
                    period_type='day',
                    start_date=start,
                    end_date=end,
                    frequency_type=bar_type,
                    frequency=bar_size,
                    extended_hours=True
                )

            # parse the candles.
            for candle in historical_prices_response['candles'][-1:]:
                new_price_mini_dict = {}
                new_price_mini_dict['symbol'] = symbol
                new_price_mini_dict['open'] = candle['open']
                new_price_mini_dict['close'] = candle['close']
                new_price_mini_dict['high'] = candle['high']
                new_price_mini_dict['low'] = candle['low']
                new_price_mini_dict['volume'] = candle['volume']
                new_price_mini_dict['datetime'] = candle['datetime']
                latest_prices.append(new_price_mini_dict)

        return latest_prices

    def wait_till_next_bar(self, last_bar_timestamp: pd.DatetimeIndex) -> None:

        last_bar_time = last_bar_timestamp.to_pydatetime()[0].replace(tzinfo=timezone.utc)
        next_bar_time = last_bar_time + timedelta(seconds=60)
        curr_bar_time = datetime.now(tz=timezone.utc)

        last_bar_timestamp = int(last_bar_time.timestamp())
        next_bar_timestamp = int(next_bar_time.timestamp())
        curr_bar_timestamp = int(curr_bar_time.timestamp())

        time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

        if time_to_wait_now < 0:
            time_to_wait_now = 0

        print("=" * 80)
        print("Pausing for the next bar")
        print("-" * 80)
        print("Curr Time: {time_curr}".format(
            time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )
        print("Next Time: {time_next}".format(
            time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        )
        print("Sleep Time: {seconds}".format(seconds=time_to_wait_now))
        print("-" * 80)
        print('')

        time_true.sleep(time_to_wait_now)

    def create_stock_frame(self, data: List[dict]) -> StockFrame:

        # Create the Frame.
        self.stock_frame = StockFrame(data=data)

        return self.stock_frame

    def execute_signals(self, signals: List[pd.Series], trades_to_execute: dict) -> List[dict]:


        # Define the Buy and sells.
        buys: pd.Series = signals['buys']
        sells: pd.Series = signals['sells']

        order_responses = []

        # If we have buys or sells continue.
        if not buys.empty:

            # Grab the buy Symbols.
            symbols_list = buys.index.get_level_values(0).to_list()

            # Loop through each symbol.
            for symbol in symbols_list:

                # Check to see if there is a Trade object.
                if symbol in trades_to_execute:

                    if self.portfolio.in_portfolio(symbol=symbol):
                        self.portfolio.set_ownership_status(
                            symbol=symbol,
                            ownership=True
                        )

                    # Set the Execution Flag.
                    trades_to_execute[symbol]['has_executed'] = True
                    trade_obj: Trade = trades_to_execute[symbol]['buy']['trade_func']

                    if not self.paper_trading:

                        # Execute the order.
                        order_response = self.execute_orders(
                            trade_obj=trade_obj
                        )

                        order_response = {
                            'order_id': order_response['order_id'],
                            'request_body': order_response['request_body'],
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

                    else:

                        order_response = {
                            'order_id': trade_obj._generate_order_id(),
                            'request_body': trade_obj.order,
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

        elif not sells.empty:

            # Grab the buy Symbols.
            symbols_list = sells.index.get_level_values(0).to_list()

            # Loop through each symbol.
            for symbol in symbols_list:

                # Check to see if there is a Trade object.
                if symbol in trades_to_execute:

                    # Set the Execution Flag.
                    trades_to_execute[symbol]['has_executed'] = True

                    if self.portfolio.in_portfolio(symbol=symbol):
                        self.portfolio.set_ownership_status(
                            symbol=symbol,
                            ownership=False
                        )

                    trade_obj: Trade = trades_to_execute[symbol]['sell']['trade_func']

                    if not self.paper_trading:

                        # Execute the order.
                        order_response = self.execute_orders(
                            trade_obj=trade_obj
                        )

                        order_response = {
                            'order_id': order_response['order_id'],
                            'request_body': order_response['request_body'],
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

                    else:

                        order_response = {
                            'order_id': trade_obj._generate_order_id(),
                            'request_body': trade_obj.order,
                            'timestamp': datetime.now().isoformat()
                        }

                        order_responses.append(order_response)

        # Save the response.
        self.save_orders(order_response_dict=order_responses)

        return order_responses

    def execute_orders(self, trade_obj: Trade) -> dict:


        # Execute the order.
        order_dict = self.session.place_order(
            account=self.trading_account,
            order=trade_obj.order
        )

        # Store the order.
        trade_obj._order_response = order_dict

        # Process the order response.
        trade_obj._process_order_response()

        return order_dict

    def save_orders(self, order_response_dict: dict) -> bool:


        def default(obj):

            if isinstance(obj, bytes):
                return str(obj)

        # Define the folder.
        folder: pathlib.PurePath = pathlib.Path(
            __file__
        ).parents[1].joinpath("data")

        # See if it exist, if not create it.
        if not folder.exists():
            folder.mkdir()

        # Define the file path.
        file_path = folder.joinpath('orders.json')

        # First check if the file alread exists.
        if file_path.exists():
            with open('data/orders.json', 'r') as order_json:
                orders_list = json.load(order_json)
        else:
            orders_list = []

        # Combine both lists.
        orders_list = orders_list + order_response_dict

        # Write the new data back.
        with open(file='data/orders.json', mode='w+') as order_json:
            json.dump(obj=orders_list, fp=order_json, indent=4, default=default)

        return True

    def get_accounts(self, account_number: str = None, all_accounts: bool = False) -> dict:


        # Depending on how the client was initalized, either use the state account
        # or the one passed through the function.
        if all_accounts:
            account = 'all'
        elif self.trading_account:
            account = self.trading_account
        else:
            account = account_number

        # Grab the accounts.
        accounts = self.session.get_accounts(
            account=account
        )

        # Parse the account info.
        accounts_parsed = self._parse_account_balances(
            accounts_response=accounts
        )

        return accounts_parsed

    def _parse_account_balances(self, accounts_response: Union[Dict, List]) -> List[Dict]:


        account_lists = []

        if isinstance(accounts_response, dict):

            account_dict = {}

            for account_type_key in accounts_response:
                account_info = accounts_response[account_type_key]

                account_id = account_info['accountId']
                account_type = account_info['type']
                account_current_balances = account_info['currentBalances']
                # account_inital_balances = account_info['initialBalances']

                account_dict['account_number'] = account_id
                account_dict['account_type'] = account_type
                account_dict['cash_balance'] = account_current_balances['cashBalance']
                account_dict['long_market_value'] = account_current_balances['longMarketValue']

                account_dict['cash_available_for_trading'] = account_current_balances.get(
                    'cashAvailableForTrading', 0.0
                )
                account_dict['cash_available_for_withdrawl'] = account_current_balances.get(
                    'cashAvailableForWithDrawal', 0.0
                )
                account_dict['available_funds'] = account_current_balances.get(
                    'availableFunds', 0.0
                )
                account_dict['buying_power'] = account_current_balances.get(
                    'buyingPower', 0.0
                )
                account_dict['day_trading_buying_power'] = account_current_balances.get(
                    'dayTradingBuyingPower', 0.0
                )
                account_dict['maintenance_call'] = account_current_balances.get(
                    'maintenanceCall', 0.0
                )
                account_dict['maintenance_requirement'] = account_current_balances.get(
                    'maintenanceRequirement', 0.0
                )

                account_dict['short_balance'] = account_current_balances.get(
                    'shortBalance', 0.0
                )
                account_dict['short_market_value'] = account_current_balances.get(
                    'shortMarketValue', 0.0
                )
                account_dict['short_margin_value'] = account_current_balances.get(
                    'shortMarginValue', 0.0
                )

                account_lists.append(account_dict)

        elif isinstance(accounts_response, list):

            for account in accounts_response:

                account_dict = {}

                for account_type_key in account:
                    account_info = account[account_type_key]

                    account_id = account_info['accountId']
                    account_type = account_info['type']
                    account_current_balances = account_info['currentBalances']
                    # account_inital_balances = account_info['initialBalances']

                    account_dict['account_number'] = account_id
                    account_dict['account_type'] = account_type
                    account_dict['cash_balance'] = account_current_balances['cashBalance']
                    account_dict['long_market_value'] = account_current_balances['longMarketValue']

                    account_dict['cash_available_for_trading'] = account_current_balances.get(
                        'cashAvailableForTrading', 0.0
                    )
                    account_dict['cash_available_for_withdrawl'] = account_current_balances.get(
                        'cashAvailableForWithDrawal', 0.0
                    )
                    account_dict['available_funds'] = account_current_balances.get(
                        'availableFunds', 0.0
                    )
                    account_dict['buying_power'] = account_current_balances.get(
                        'buyingPower', 0.0
                    )
                    account_dict['day_trading_buying_power'] = account_current_balances.get(
                        'dayTradingBuyingPower', 0.0
                    )
                    account_dict['maintenance_call'] = account_current_balances.get(
                        'maintenanceCall', 0.0
                    )
                    account_dict['maintenance_requirement'] = account_current_balances.get(
                        'maintenanceRequirement', 0.0
                    )
                    account_dict['short_balance'] = account_current_balances.get(
                        'shortBalance', 0.0
                    )
                    account_dict['short_market_value'] = account_current_balances.get(
                        'shortMarketValue', 0.0
                    )
                    account_dict['short_margin_value'] = account_current_balances.get(
                        'shortMarginValue', 0.0
                    )

                    account_lists.append(account_dict)

        return account_lists

    def get_positions(self, account_number: str = None, all_accounts: bool = False) -> List[Dict]:


        if all_accounts:
            account = 'all'
        elif self.trading_account and account_number is None:
            account = self.trading_account
        else:
            account = account_number

        # Grab the positions.
        positions = self.session.get_accounts(
            account=account,
            fields=['positions']
        )

        # Parse the positions.
        positions_parsed = self._parse_account_positions(
            positions_response=positions
        )

        return positions_parsed

    def _parse_account_positions(self, positions_response: Union[List, Dict]) -> List[Dict]:


        positions_lists = []

        if isinstance(positions_response, dict):

            for account_type_key in positions_response:

                account_info = positions_response[account_type_key]

                account_id = account_info['accountId']
                positions = account_info['positions']

                for position in positions:
                    position_dict = {}
                    position_dict['account_number'] = account_id
                    position_dict['average_price'] = position['averagePrice']
                    position_dict['market_value'] = position['marketValue']
                    position_dict['current_day_profit_loss_percentage'] = position['currentDayProfitLossPercentage']
                    position_dict['current_day_profit_loss'] = position['currentDayProfitLoss']
                    position_dict['long_quantity'] = position['longQuantity']
                    position_dict['short_quantity'] = position['shortQuantity']
                    position_dict['settled_long_quantity'] = position['settledLongQuantity']
                    position_dict['settled_short_quantity'] = position['settledShortQuantity']

                    position_dict['symbol'] = position['instrument']['symbol']
                    position_dict['cusip'] = position['instrument']['cusip']
                    position_dict['asset_type'] = position['instrument']['assetType']
                    position_dict['sub_asset_type'] = position['instrument'].get(
                        'subAssetType', ""
                    )
                    position_dict['description'] = position['instrument'].get(
                        'description', ""
                    )
                    position_dict['type'] = position['instrument'].get(
                        'type', ""
                    )

                    positions_lists.append(position_dict)

        elif isinstance(positions_response, list):

            for account in positions_response:

                for account_type_key in account:

                    account_info = account[account_type_key]

                    account_id = account_info['accountId']
                    positions = account_info['positions']

                    for position in positions:
                        position_dict = {}
                        position_dict['account_number'] = account_id
                        position_dict['average_price'] = position['averagePrice']
                        position_dict['market_value'] = position['marketValue']
                        position_dict['current_day_profit_loss_percentage'] = position['currentDayProfitLossPercentage']
                        position_dict['current_day_profit_loss'] = position['currentDayProfitLoss']
                        position_dict['long_quantity'] = position['longQuantity']
                        position_dict['short_quantity'] = position['shortQuantity']
                        position_dict['settled_long_quantity'] = position['settledLongQuantity']
                        position_dict['settled_short_quantity'] = position['settledShortQuantity']

                        position_dict['symbol'] = position['instrument']['symbol']
                        position_dict['cusip'] = position['instrument']['cusip']
                        position_dict['asset_type'] = position['instrument']['assetType']
                        position_dict['sub_asset_type'] = position['instrument'].get(
                            'subAssetType', ""
                        )
                        position_dict['description'] = position['instrument'].get(
                            'description', ""
                        )
                        position_dict['type'] = position['instrument'].get(
                            'type', ""
                        )

                        positions_lists.append(position_dict)

        return positions_lists