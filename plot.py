import pandas as pd
import numpy as np


data = pd.read_csv("data/QQQ.csv")
price_data = data[['High','Low','Close']]

box_size = 10
reversal_size = 3
# scale = generate_scale(start=np.floor(price_data['Low'].min()), end=np.ceil(price_data['High'].max()), box_size=box_size)
scale = np.arange(260,430, 10)


def generate_column_range(scale, range_low, range_high):
    '''
    Takes in the high and low extremes of a box range and returns the whole
    range as a np.array

    Args:
        scale: np.array
        range_low: int or float
        range_high: into or float

    Returns:
        col_range: np.array
    '''
    col_range = scale[np.logical_and(scale>=range_low, scale<=range_high)]
    
    return col_range 

# review this function:
def generate_scale(start, end, box_size=1, method='standard'):
    scale = np.arange(start=start, stop=high+box_size, step=box_size)
    
    return scale

def init_pnf(scale,
             high,
             low,
             close,
             reversal_size,
             box_range=[]):
    '''
    returns trend status as num value (either 0, 1 or -1) and box_range as np.array
    
    Args:
        scale: np.array - the scale for the chart
        high: float - high price
        low: float  - low price
        close: float - closing/last price
        reversal_size: int > 0
        box_range: np.array or empty list
        
    Returns:
        status: int (-1,0, or 1)
        box_range: np.array
    '''
    
    if len(box_range) == 0:
        box_range = scale[np.logical_and(scale>=low, scale<=high)]
    else:
        box_range = scale[np.logical_and(scale>=min(box_range.min(), low), scale<=max(box_range.max(), high))]
#         box_range = generate_column_range()
        
    mid_price = 0.5 * box_range.min() + 0.5 * box_range.max()

    if len(box_range) >= reversal_size and close > mid_price:
        status = 1
    elif len(box_range) >= reversal_size and close < mid_price:
        status = -1
    else:
        status = 0
        
    return status, box_range

def update_pnf(scale,
               high,
               low,
               status,
               reversal_size,
               box_low,
               box_high):
    '''
    updates the chart once the trend status is defined
    returns status and box_range for the day
    
    Args:
        scale:
        high:
        low:
        status:
        reversal_size:
        box_low:
        box_high:
    Returns:
        status: int (-1,0, or 1)
        box_range: np.array
    '''
#     box_range = scale[np.logical_and(scale>=box_low, scale<=box_high)] # needed in case we return the current range
    box_range = generate_column_range(scale, box_low, box_high)
    box_reverse = []
    # new temporary box range with extensions on both sides:
#     box_range_new = scale[np.logical_and(scale>=min(low, box_low), scale<=max(high, box_high))]
    box_range_new = generate_column_range(scale, min(low, box_low), max(high, box_high))
    box_high_new = box_range_new.max()
    box_low_new = box_range_new.min()
    
    if status == 1:
        # check for upper extensions, else for reversals
        if box_high_new > box_high:
            box_range = scale[np.logical_and(scale>=box_low, scale<=box_high_new)]
#             use generate_...()
        # check for potential reversal
        elif low < box_high:
            box_reverse = scale[np.logical_and(scale>=low, scale<=box_high)][:-1]    
#             use generate_...()
                  
    if status == -1:
        if box_low_new < box_low:
            box_range = scale[np.logical_and(scale>=box_low_new, scale<=box_high)]
        elif high > box_low:
            box_reverse = scale[np.logical_and(scale>=box_low, scale<=high)][1:]

    # Check potentiall reversal agains reversal_size and reverse status if needed:      
    if len(box_reverse) >= reversal_size:
        status *= -1 # reverse trend status
        box_range = box_reverse # update box_range
    
    return status, box_range

def pnf_text(scale, columns):
    '''
    Generates a text PnF chart
    
    Args:
        scale: np.array
        columns: list of tuples (int, np.array)
    Returns:
        grid: multiline string with lines separated by linefeed
    '''
    hpad = 2 # padding columns on the sides
    marker = {0:'*', 1:'X', -1:'O'}
    grid = ""

    for line_price in np.flip(scale):
        line = f'{line_price}' + '.'*hpad
        for col in columns:
            line += marker[col[0]] if line_price in col[1] else '.'
        line += '.' * hpad + f'{line_price}\n'
        grid += line
    
    return grid


def process_pnf(price_data, scale, reversal_size):

    # initialise status and box arrays:
    trend_status = np.zeros(len(price_data))
    box_low = np.zeros(len(price_data))
    box_high = np.zeros(len(price_data))

    # Initialise the chart until a trend status (+/-1) is found
    box_range = []
    for index, row in enumerate(price_data.iterrows()):
        high = row[1]['High']
        low = row[1]['Low']
        close = row[1]['Close']
        status, box_range = init_pnf(scale, high, low, close, reversal_size, box_range)
        trend_status[index] = status
        box_low[index] = box_range.min()
        box_high[index] = box_range.max()
        if status != 0:
            break

    # Check if there are more lines of data to process
    # print(index + 1 < len(price_data))
    # return column if not true

    # Next, we need to process the remaining lines of price:
    start = index + 1
    for index, row in enumerate(price_data.loc[start:].iterrows()):
        high = row[1]['High']
        low = row[1]['Low']
        status = trend_status[index + start - 1]
        box_l = box_low[index + start - 1]
        box_h = box_high[index + start - 1]
        status, box_range = update_pnf(scale, high, low, status, reversal_size, box_l, box_h)
        trend_status[index+start] = status
        box_low[index+start] = box_range.min()
        box_high[index+start] = box_range.max()

    pnf_data = pd.DataFrame({'trend_status': trend_status,
                            'range_low': box_low,
                            'range_high': box_high
                            })

# I could take this out into a new function (taking pnf_data in):

    changes = (np.diff(np.sign(trend_status)) != 0)
    # We make sure that the a column is generated for the last price line:
    changes = np.append(changes, [True])
    # Note that the change column is 'shifted': it's True when a status change is detected on the next price line:
    pnf_data['change'] = changes

    ranges = []
    trends = []

    # should we use .apply() here?
    for row in pnf_data[pnf_data['change']].iterrows():
        row = row[1]
        col_range = generate_column_range(scale, row['range_low'], row['range_high'])
        ranges.append(col_range)
        trends.append(row['trend_status'])

    columns = list(zip(trends, ranges))

    return columns

def get_chart(): # args needed!
    # args: data file, scale method, box_size, reversal_size, plot method (hl vs last)
    # should scale be generated here?
    columns = process_pnf(price_data, scale, reversal_size)

    return columns


if __name__ == '__main__':
    columns = get_chart()
    print(pnf_text(scale, columns))