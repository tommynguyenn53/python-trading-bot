from pyrobot.trades import Trade
from td.client import TDClient

class OrderStatus():

    def __init__(self, trade_obj: Trade) -> None:

        self.trade_obj = trade_obj
        self.order_status = self.trade_obj.order_status

    @property
    def is_cancelled(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'FILLED':
            return True
        else:
            return False

    @property
    def is_rejected(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'REJECTED':
            return True
        else:
            return False

    @property
    def is_expired(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'EXPIRED':
            return True
        else:
            return False

    @property
    def is_replaced(self, refresh_order_info: bool = True) -> bool:

        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'REPLACED':
            return True
        else:
            return False

    @property
    def is_working(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'WORKING':
            return True
        else:
            return False

    @property
    def is_pending_activation(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'PENDING_ACTIVATION':
            return True
        else:
            return False

    @property
    def is_pending_cancel(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'PENDING_CANCEL':
            return True
        else:
            return False

    @property
    def is_pending_replace(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'PENDING_REPLACE':
            return True
        else:
            return False

    @property
    def is_queued(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'QUEUED':
            return True
        else:
            return False

    @property
    def is_accepted(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'ACCEPTED':
            return True
        else:
            return False

    @property
    def is_awaiting_parent_order(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'AWAITING_PARENT_ORDER':
            return True
        else:
            return False

    @property
    def is_awaiting_condition(self, refresh_order_info: bool = True) -> bool:


        if refresh_order_info:
            self.trade_obj._update_order_status()

        if self.order_status == 'AWAITING_CONDITION':
            return True
        else:
            return False