from datetime import datetime
from itertools import count
import time
import MetaTrader5 as mt5

CRYPTO = 'BTCUSD'

PRICE_THRESHOLD = 2 # 2% price threshold
STOP_LOSS = 4 # 4% stop loss
TAKE_PROFIT = 10 # take profit at 10%

# replace to choose between buy/sell order
BUY = mt5.ORDER_TYPE_BUY
SELL = mt5.ORDER_TYPE_SELL
ORDER_TYPE = BUY

mt5.initialize()

account_number = 3009024
authorized = mt5.login(account_number)

if authorized:
    print(f'CONNECTED TO ACCOUNT #{account_number}')
else:
    print(f'FAILED TO CONNECT TO ACCOUNT #{account_number}, ERROR CODE: {mt5.last_error()}'

# store equity of account
account_info = mt5.account_info()
if account_info is None:
    raise RuntimeError('COULD NOT LOAD THE ACCOUNT EQUITY LEVEL.')
else:
    equity = float(account_info[10])

def get_dates():
    """Use dates to define the range of our dataset in get_data()"""
    today = datetime.today()
    utc_from = datetime(year=today.year, month=today.month, day=today.day-1)
    return utc_from, datetime.now()

def get_data():
    """Download one day's worth of ten minute candles, along with buy/sell prices for BTC"""
    utc_from, utc_to = get_dates()
    return mt5.copy_rates_range('BTCUSD', mt5.TIMEFRAME_M10, utc_from, utc_to)

def get_current_prices():
    """Returns current buy/sell prices for BTC"""
    current_buy_price = mt5.symbol_info_tick("BTCUSD")[2]
    current_sell_price = mt5.symbol_info_tick("BTCUSD")[1]
    return current_buy_price, current_sell_price

def trade():
    """Determines whether to trade and if so, sends trade to MT5"""
    
    # collects necessary data from other functions
    utc_from, utc_to = get_dates()
    candles = get_data()
    current_buy_price, current_sell_price = get_current_prices()

    # calculates % difference between current price and close price of previous candle
    difference = (candles['close'][-1] - candles['close'][-2]) / candles['close'][-2] * 100

    # check if position already placed
    positions = mt5.positions_get(symbol=CRYPTO)
    orders = mt5.orders_get(symbol=CRYPTO)
    symbol_info = mt5.symbol_info(CRYPTO)

    # perform logic check
    if difference > PRICE_THRESHOLD:
        print(f'dif 1: {CRYPTO}, {difference}')
        # pause to check if increase stays
        time.sleep(8)

        candles = mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)
        difference = (candles['close'][-1] - candles['close'][-2]) / candles['close'][-2]*100
        if difference > PRICE_THRESHOLD:
            print(f'dif 2: {CRYPTO}, {difference}')
            price = mt5.symbol_info_tick(CRYPTO).bid
            print(f'{CRYPTO} is up {str(difference)}% in the last 5 minutes, opening BUY position.')

            # prepare trade request
            if not mt5.initialize():
                raise RuntimeError(f'MT5 initialize() failed with error code {mt5.last_error()}')
                
            # check to make sure there are no open positions/orders
            if len(positions) == 0 and len(orders) < 1:
                if symbol_info is None:
                    print(f'{CRYPTO} not found, cannot call order_check()')
                    mt5.shutdown()
                if not symbol_info.visible:
                    print(f'{CRYPTO} is not visible, trying to switch on')
                    if not mt5.symbol_select(CRYPTO, True):
                        print('symbol_select({}) failed, exit', CRYPTO)

                lot = float(round(((equity/20) / current_buy_price), 2))
                if ORDER_TYPE == BUY:
                    stop = price - (price*STOP_LOSS) / 100
                    sell = price + (price*TAKE_PROFIT) / 100
                else:
                    stop = price + (price*STOP_LOSS) / 100
                    sell = price - (price*TAKE_PROFIT) / 100

                request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'symbol': CRYPTO,
                    'volume': lot,
                    'type': ORDER_TYPE,
                    'price': price,
                    'sl': stop,
                    'tp': sell
                    'magic': 66,
                    'comment': 'python-buy',
                    'type_time': mt5.ORDER_TIME_GTC,
                    'type_filling': mt5.ORDER_FILLING_IOC,
                }

                # send request to trade
                res = mt5.order_send(request)

                print(f'1. order_send(): by {CRYPTO} {lot} lots at {price}')

                if res.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f'2. order_send failed, retcode={res.retcode}')

                # print order result
                print(f'2. order_send done, {res}')
                print(f'opened position with POSITION_TICKET={res.order}')

            else:
                print(f'BUY signal detected, but {CRYPTO} has {len(positions)} active trades')
        
        else:
            pass

    else:
        if orders or positions:
            print('Buying signal detected but there is already an active trade')
        else:
            print(f'difference is only: {str(difference)}% trying again...')

if __name__ = '__main__':
    print('Press Ctrl-C to stop.')
    for i in count():
        trade()
        print(f'Iteration {i}')