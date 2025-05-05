import json
from datetime import datetime

from typing import List
from typing import Dict

from td.client import TDClient


class Trade():


    def __init__(self):

        self.order = {}
        self.trade_id = ""
        self.order_id = ""
        self.account = ""
        self.order_status = "NOT_PLACED"

        self.side = ""
        self.side_opposite = ""
        self.enter_or_exit = ""
        self.enter_or_exit_opposite = ""

        self._order_response = {}
        self._triggered_added = False
        self._multi_leg = False
        self._one_cancels_other = False
        self._td_client: TDClient = None

    def to_dict(self) -> dict:

        # Initialize the Dict.
        obj_dict = {
            "__class___": self.__class__.__name__,
            "__module___": self.__module__
        }

        # Add the Object.
        obj_dict.update(self.__dict__)

        return obj_dict

    def new_trade(self, trade_id: str, order_type: str, side: str, enter_or_exit: str, price: float = 0.00,
                  stop_limit_price: float = 0.00) -> dict:

        self.trade_id = trade_id

        self.order_types = {
            'mkt': 'MARKET',
            'lmt': 'LIMIT',
            'stop': 'STOP',
            'stop_lmt': 'STOP_LIMIT',
            'trailing_stop': 'TRAILING_STOP'
        }

        self.order_instructions = {
            'enter': {
                'long': 'BUY',
                'short': 'SELL_SHORT'
            },
            'exit': {
                'long': 'SELL',
                'short': 'BUY_TO_COVER'
            }
        }

        self.order = {
            "orderStrategyType": "SINGLE",
            "orderType": self.order_types[order_type],
            "session": "NORMAL",
            "duration": "DAY",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[enter_or_exit][side],
                    "quantity": 0,
                    "instrument": {
                        "symbol": None,
                        "assetType": None
                    }
                }
            ]
        }

        if self.order['orderType'] == 'STOP':
            self.order['stopPrice'] = price

        elif self.order['orderType'] == 'LIMIT':
            self.order['price'] = price

        elif self.order['orderType'] == 'STOP_LIMIT':
            self.order['price'] = stop_limit_price
            self.order['stopPrice'] = price

        elif self.order['orderType'] == 'TRAILING_STOP':
            self.order['stopPriceLinkBasis'] = ""
            self.order['stopPriceLinkType'] = ""
            self.order['stopPriceOffset'] = 0.00
            self.order['stopType'] = 'STANDARD'

        # Make a refrence to the side we take, useful when adding other components.
        self.enter_or_exit = enter_or_exit
        self.side = side
        self.order_type = order_type
        self.price = price

        # If it's a stop limit order or stop order, set the stop price.
        if self.is_stop_order or self.is_stop_limit_order:
            self.stop_price = price
        else:
            self.stop_price = 0.0

        # If it's a stop limit order set the stop limit price.
        if self.is_stop_limit_order:
            self.stop_limit_price = stop_limit_price
        else:
            self.stop_limit_price = 0.0

        # If it's a limit price set the limit price.
        if self.is_limit_order:
            self.limit_price = price
        else:
            self.limit_price = 0.0

        # Set the enter or exit state.
        if self.enter_or_exit == 'enter':
            self.enter_or_exit_opposite = 'exit'
        if self.enter_or_exit == 'exit':
            self.enter_or_exit_opposite = 'enter'

        # Set the side state.
        if self.side == 'long':
            self.side_opposite = 'short'
        if self.side == 'short':
            self.side_opposite = 'long'

        return self.order

    def instrument(self, symbol: str, quantity: int, asset_type: str, sub_asset_type: str = None,
                   order_leg_id: int = 0) -> dict:


        leg = self.order['orderLegCollection'][order_leg_id]

        leg['instrument']['symbol'] = symbol
        leg['instrument']['assetType'] = asset_type
        leg['quantity'] = quantity

        self.order_size = quantity
        self.symbol = symbol
        self.asset_type = asset_type

        return leg

    def add_option_instrument(self, symbol: str, quantity: int, order_leg_id: int = 0) -> dict:


        self.instrument(
            symbol=symbol,
            quantity=quantity,
            asset_type='OPTION',
            order_leg_id=order_leg_id
        )

        leg = self.order['orderLegCollection'][order_leg_id]

        return leg

    def good_till_cancel(self, cancel_time: datetime) -> None:


        self.order['duration'] = 'GOOD_TILL_CANCEL'
        self.order['cancelTime'] = cancel_time.isoformat()

    def modify_side(self, side: str, leg_id: int = 0) -> None:


        # Validate the Side.
        if side and side not in ['buy', 'sell', 'sell_short', 'buy_to_cover', 'sell_to_close', 'buy_to_open']:
            raise ValueError(
                "The side you have specified is not valid. Please choose a valid side: ['buy', 'sell', 'sell_short', 'buy_to_cover','sell_to_close', 'buy_to_open']"
            )

        # Set the Order.
        if side:
            self.order['orderLegCollection'][leg_id]['instruction'] = side.upper()
        else:
            self.order['orderLegCollection'][leg_id]['instruction'] = self.order_instructions[self.enter_or_exit][
                self.side_opposite]

    def add_box_range(self, profit_size: float = 0.00, stop_size: float = 0.00,
                      stop_percentage: bool = False, profit_percentage: bool = False,
                      stop_limit: bool = False, make_one_cancels_other: bool = True,
                      limit_size: float = 0.00, limit_percentage: bool = False):


        if not self._triggered_added:
            self._convert_to_trigger()

        # Add a take profit Limit order.
        self.add_take_profit(
            profit_size=profit_size,
            percentage=profit_percentage
        )

        # Add a stop Loss Order.
        if not stop_limit:
            self.add_stop_loss(
                stop_size=profit_size,
                percentage=stop_percentage
            )
        else:
            self.add_stop_limit(
                stop_size=profit_size,
                limit_size=limit_size,
                stop_percentage=stop_percentage,
                limit_percentage=limit_percentage
            )

        if make_one_cancels_other:
            self.add_one_cancels_other()

        self.is_box_range = True

    def add_stop_loss(self, stop_size: float, percentage: bool = False) -> bool:


        if not self._triggered_added:
            self._convert_to_trigger()

        price = self.grab_price()

        if percentage:
            adjustment = 1.0 - stop_size
            new_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=True
            )
        else:
            adjustment = -stop_size
            new_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=False
            )

        stop_loss_order = {
            "orderType": "STOP",
            "session": "NORMAL",
            "duration": "DAY",
            "stopPrice": new_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        self.stop_loss_order = stop_loss_order
        self.order['childOrderStrategies'].append(self.stop_loss_order)

        return True

    def add_stop_limit(self, stop_size: float, limit_size: float, stop_percentage: bool = False,
                       limit_percentage: bool = False):


        # Check to see if there is a trigger.
        if not self._triggered_added:
            self._convert_to_trigger()

        price = self.grab_price()

        # Calculate the Stop Price.
        if stop_percentage:
            adjustment = 1.0 - stop_size
            stop_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=True
            )
        else:
            adjustment = -stop_size
            stop_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=False
            )

        # Calculate the Limit Price.
        if limit_percentage:
            adjustment = 1.0 - limit_size
            limit_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=True
            )
        else:
            adjustment = -limit_size
            limit_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=False
            )

        # Add the order.
        stop_limit_order = {
            "orderType": "STOP_LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "price": limit_price,
            "stopPrice": stop_price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        self.stop_limit_order = stop_limit_order
        self.order['childOrderStrategies'].append(self.stop_limit_order)

        return True

    def _calculate_new_price(self, price: float, adjustment: float, percentage: bool) -> float:

        if percentage:
            new_price = price * adjustment
        else:
            new_price = price + adjustment

        # For orders below $1.00, can only have 4 decimal places.
        if new_price < 1:
            new_price = round(new_price, 4)

        # For orders above $1.00, can only have 2 decimal places.
        else:
            new_price = round(new_price, 2)

        return new_price

    def grab_price(self) -> float:


        # We need to basis to calculate off of. Use the price.
        if self.order_type == 'mkt':

            quote = self._td_client.get_quotes(instruments=[self.symbol])

            # Have to make a call to Get Quotes.
            price = quote[self.symbol]['lastPrice']

        elif self.order_type == 'lmt':
            price = self.price

        else:

            quote = self._td_client.get_quotes(instruments=[self.symbol])

            # Have to make a call to Get Quotes.
            price = quote[self.symbol]['lastPrice']

        return round(price, 2)

    def add_take_profit(self, profit_size: float, percentage: bool = False) -> bool:


        # Check to see if we have a trigger order.
        if not self._triggered_added:
            self._convert_to_trigger()

        price = self.grab_price()

        # Calculate the new price.
        if percentage:
            adjustment = 1.0 + profit_size
            new_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=True
            )
        else:
            adjustment = profit_size
            new_price = self._calculate_new_price(
                price=price,
                adjustment=adjustment,
                percentage=False
            )

        # Build the order.
        take_profit_order = {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": new_price,
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": self.order_instructions[self.enter_or_exit_opposite][self.side],
                    "quantity": self.order_size,
                    "instrument": {
                        "symbol": self.symbol,
                        "assetType": self.asset_type
                    }
                }
            ]
        }

        # Add the order.
        self.take_profit_order = take_profit_order
        self.order['childOrderStrategies'].append(self.take_profit_order)

        return True

    def add_one_cancels_other(self, orders: List[Dict] = None) -> Dict:

        # Define the OCO Template
        new_temp = [
            {
                'orderStrategyType': "OCO",
                'childOrderStrategies': []
            }
        ]

        # If we alread have a trigger than their are orders there.
        if self._triggered_added:
            # Grab the old ones.
            old_orders = self.order['childOrderStrategies']

            # Add them to the template.
            new_temp[0]['childOrderStrategies'] = old_orders

            # Set the new child order strategy.
            self.order['childOrderStrategies'] = new_temp

        # Set it so we know it's a One Cancels Other.
        self._one_cancels_other = True

    def _convert_to_trigger(self):


        # Only convert to a trigger order, if it already isn't one.
        if self.order and not self._triggered_added:
            self.order['orderStrategyType'] = 'TRIGGER'

            # Trigger orders will have child strategies, so initalize that list.
            self.order['childOrderStrategies'] = []

            # Update the state.
            self._triggered_added = True

    def modify_session(self, session: str) -> None:


        if session in ['am', 'pm', 'normal', 'seamless']:
            self.order['session'] = session.upper()
        else:
            raise ValueError(
                'Invalid session, choose either am, pm, normal, or seamless')

    @property
    def order_response(self) -> dict:


        return self._order_response

    @order_response.setter
    def order_response(self, order_response_dict: dict) -> None:

        self._order_response = order_response_dict

    def _generate_order_id(self) -> str:

        # If we have an order, then generate it.
        if self.order:

            order_id = "{symbol}_{side}_{enter_or_exit}_{timestamp}"

            order_id = order_id.format(
                symbol=self.symbol,
                side=self.side,
                enter_or_exit=self.enter_or_exit,
                timestamp=datetime.now().timestamp()
            )

            return order_id

        else:
            return ""

    def add_leg(self, order_leg_id: int, symbol: str, quantity: int, asset_type: str, sub_asset_type: str = None) -> \
    List[dict]:


        # Define the leg.
        leg = {}
        leg['instrument']['symbol'] = symbol
        leg['instrument']['assetType'] = asset_type
        leg['quantity'] = quantity

        if sub_asset_type:
            leg['instrument']['subAssetType'] = sub_asset_type

        # If 0, call instrument.
        if order_leg_id == 0:
            self.instrument(
                symbol=symbol,
                asset_type=asset_type,
                quantity=quantity,
                sub_asset_type=sub_asset_type,
                order_leg_id=0
            )
        else:
            # Insert it.
            order_leg_colleciton: list = self.order['orderLegCollection']
            order_leg_colleciton.insert(order_leg_id, leg)

        return self.order['orderLegCollection']

    @property
    def number_of_legs(self) -> int:


        return len(self.order['orderLegCollection'])

    def modify_price(self, new_price: float, price_type: str) -> None:


        if price_type == 'price':
            self.order['price'] = new_price
        elif price_type == 'stop-price' and self.is_stop_order:
            self.order['stopPrice'] = new_price
            self.stop_price = new_price
        elif price_type == 'limit-price' and self.is_limit_order:
            self.order['price'] = new_price
            self.price = new_price
        elif price_type == 'stop-limit-limit-price' and self.is_stop_limit_order:
            self.order['price'] = new_price
            self.stop_limit_price = new_price
        elif price_type == 'stop-limit-stop-price' and self.is_stop_limit_order:
            self.order['stopPrice'] = new_price
            self.stop_price = new_price

    @property
    def is_stop_order(self) -> bool:


        if self.order_type != 'stop':
            return False
        else:
            return True

    @property
    def is_stop_limit_order(self) -> bool:


        if self.order_type != 'stop-lmt':
            return False
        else:
            return True

    @property
    def is_limit_order(self) -> bool:


        if self.order_type != 'lmt':
            return False
        else:
            return True

    @property
    def is_trigger_order(self) -> bool:


        if self._triggered_added:
            return True
        else:
            return False

    def _process_order_response(self) -> None:

        self.order_id = self._order_response["order_id"]
        self.order_status = "QUEUED"

    def _update_order_status(self) -> None:

        if self.order_id != "":
            order_response = self._td_client.get_orders(
                account=self.account,
                order_id=self.order_id
            )

            self.order_response = order_response
            self.order_status = self.order_response['status']

    def check_status(self) -> object:


        from pyrobot.order_status import OrderStatus

        return OrderStatus(trade_obj=self)

    def update_children(self) -> None:

        # Grab the children.
        children = self.order['childOrderStrategies'][0]['childOrderStrategies']

        # Loop through each child.
        for order in children:

            # Get the latest price.
            quote = self._td_client.get_quotes(instruments=[self.symbol])
            last_price = quote[self.symbol]['lastPrice']

            # Update the price.
            if order['orderType'] == 'STOP':
                order['stopPrice'] = round(order['stopPrice'] + last_price, 2)
            elif order['orderType'] == 'LIMIT':
                order['price'] = round(order['price'] + last_price, 2)