import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from scipy.signal import argrelextrema
from collections import deque
import talib

def getHigherHighs(data: np.array, order=5, K=2):
  '''
  Finds consecutive higher highs in price pattern.
  Must not be exceeded within the number of periods indicated by the width 
  parameter for the value to be confirmed.
  K determines how many consecutive highs need to be higher.
  '''
  # Get highs
  high_idx = argrelextrema(data, np.greater, order=order)[0]
  highs = data[high_idx]
  # Ensure consecutive highs are higher than previous highs
  extrema = []
  ex_deque = deque(maxlen=K)
  for i, idx in enumerate(high_idx):
    if i == 0:
      ex_deque.append(idx)
      continue
    if highs[i] < highs[i-1]:
      ex_deque.clear()
    ex_deque.append(idx)
    if len(ex_deque) == K:
      extrema.append(ex_deque.copy())
  
  return extrema

def getLowerHighs(data: np.array, order=5, K=2):
  '''
  Finds consecutive lower highs in price pattern.
  Must not be exceeded within the number of periods indicated by the width 
  parameter for the value to be confirmed.
  K determines how many consecutive highs need to be lower.
  '''
  # Get highs
  high_idx = argrelextrema(data, np.greater, order=order)[0]
  highs = data[high_idx]
  # Ensure consecutive highs are lower than previous highs
  extrema = []
  ex_deque = deque(maxlen=K)
  for i, idx in enumerate(high_idx):
    if i == 0:
      ex_deque.append(idx)
      continue
    if highs[i] > highs[i-1]:
      ex_deque.clear()
    ex_deque.append(idx)
    if len(ex_deque) == K:
      extrema.append(ex_deque.copy())
  return extrema

def getLowerLows(data: np.array, order=5, K=2):
  '''
  Finds consecutive lower lows in price pattern.
  Must not be exceeded within the number of periods indicated by the width 
  parameter for the value to be confirmed.
  K determines how many consecutive lows need to be lower.
  '''
  # Get lows
  low_idx = argrelextrema(data, np.less, order=order)[0]
  lows = data[low_idx]
  # Ensure consecutive lows are lower than previous lows
  extrema = []
  ex_deque = deque(maxlen=K)
  for i, idx in enumerate(low_idx):
    if i == 0:
      ex_deque.append(idx)
      continue
    if lows[i] > lows[i-1]:
      ex_deque.clear()

    ex_deque.append(idx)
    if len(ex_deque) == K:
      extrema.append(ex_deque.copy())

  return extrema

def getHigherLows(data: np.array, order=5, K=2):
  '''
  Finds consecutive higher lows in price pattern.
  Must not be exceeded within the number of periods indicated by the width 
  parameter for the value to be confirmed.
  K determines how many consecutive lows need to be higher.
  '''
  # Get lows
  low_idx = argrelextrema(data, np.less, order=order)[0]
  lows = data[low_idx]
  # Ensure consecutive lows are higher than previous lows
  extrema = []
  ex_deque = deque(maxlen=K)
  for i, idx in enumerate(low_idx):
    if i == 0:
      ex_deque.append(idx)
      continue
    if lows[i] < lows[i-1]:
      ex_deque.clear()

    ex_deque.append(idx)
    if len(ex_deque) == K:
      extrema.append(ex_deque.copy())

  return extrema


# đã có edit, chỉ cộng period 5 vào cho đỉnh cuối cùng
def getHHIndex(data: np.array, order=5, K=2):
  extrema = getHigherHighs(data, order, K)
  extrema_lated = extrema[-1][-1]
  if extrema_lated +order > len(data):
    extrema.remove(extrema_lated)
  idx = np.array([i[-1]  for i in extrema])
  return idx

def getLHIndex(data: np.array, order=5, K=2):
  extrema = getLowerHighs(data, order, K)
  extrema_lated = extrema[-1][-1]
  for i in range(len(extrema) - 1, -1, -1):
    deq = extrema[i]
    if extrema_lated in deq:
        extrema.pop(i)
        break
  idx = np.array([i[-1]  for i in extrema])
  return idx
  



def getLLIndex(data: np.array, order=5, K=2):
  extrema = getLowerLows(data, order, K)
  extrema_lated = extrema[-1][-1]
  if extrema_lated +order > len(data):
    extrema.remove(extrema_lated)
  idx = np.array([i[-1]  for i in extrema])
  return idx
  

def getHLIndex(data: np.array, order=5, K=2):
  extrema = getHigherLows(data, order, K)
  extrema_lated = extrema[-1][-1]
  if extrema_lated +order > len(data):
    extrema.remove(extrema_lated)
  idx = np.array([i[-1]  for i in extrema])
  return idx
  

def getPeaks(data, key='close', order=5, K=2, P=20):
  data =data.sort_values('date').reset_index(drop = True)
  vals = data[key].values
  hh_idx = getHHIndex(vals, order, K)
  lh_idx = getLHIndex(vals, order, K)
  ll_idx = getLLIndex(vals, order, K)
  hl_idx = getHLIndex(vals, order, K)
  data[f'{key}_highs'] = np.nan
  data[f'{key}_highs'][hh_idx] = 100
  data[f'{key}_highs'][lh_idx] = -100
  data[f'{key}_highs_adjusted'] = np.nan
  last_100_count = 0
  last_minus_100_count = 0
  count =0
  for i in range(len(data)):
      if data.loc[i, f'{key}_highs'] == 100:
          last_100_count += 1
          last_minus_100_count = 0
          count =0
      elif data.loc[i, f'{key}_highs'] == -100:
          last_minus_100_count += 1
          last_100_count = 0
          count =0
    
      if last_100_count >= 2 and count <=20:
          data.loc[i, f'{key}_highs_adjusted'] = 1
          count +=1 

      elif last_minus_100_count >= 2 and count <=P:
          data.loc[i, f'{key}_highs_adjusted'] = -1
          count +=1 
      else:
          data.loc[i, f'{key}_highs_adjusted'] = 0
  
  data[f'{key}_lows'] = np.nan
  data[f'{key}_lows'][ll_idx] = 100
  data[f'{key}_lows'][hl_idx] = -100
  data[f'{key}_lows_adjusted'] = np.nan
  
  last_100_count = 0
  last_minus_100_count = 0
  count =0
  for i in range(len(data)):
      if data.loc[i, f'{key}_lows'] == 100:
          last_100_count += 1
          last_minus_100_count = 0
          count =0
      elif data.loc[i, f'{key}_lows'] == -100:
          last_minus_100_count += 1
          last_100_count = 0
          count =0
    
      if last_100_count >= 2 and count <=20:
          data.loc[i, f'{key}_lows_adjusted'] = 1
          count +=1 

      elif last_minus_100_count >= 2 and count <=P:
          data.loc[i, f'{key}_lows_adjusted'] = -1
          count +=1 
      else:
          data.loc[i, f'{key}_lows_adjusted'] = 0
  return data







def RSIDivergenceStrategy(data , order=5, K=2,P=20):
    # Tính toán cực đại của giá và RSI
    data = getPeaks(data, key='close', order=order, K=K)
    data['RSI'] = talib.RSI(data['close'].values, timeperiod=P)
    data = getPeaks(data, key='RSI', order=order, K=K)
    data['signal'] = ''
    for i in range(1, len(data)):
        if not np.isnan(data.at[i, 'RSI']):
            if data.at[i, 'close_lows_adjusted'] == -1 and data.at[i, 'RSI_lows_adjusted'] == 1 and data.at[i, 'RSI'] < 50:
                data.at[i, 'signal'] = 'Bullish Divergence'
            elif data.at[i, 'close_highs_adjusted'] == 1 and data.at[i, 'RSI_highs_adjusted'] == -1 and data.at[i, 'RSI'] > 50:
                data.at[i, 'signal'] = 'Bearish Divergence'
            elif data.at[i, 'close_lows_adjusted'] == 1 and data.at[i, 'RSI_lows_adjusted'] == -1:
                data.at[i, 'signal'] = 'Hidden Bullish Divergence'
            elif data.at[i, 'close_highs_adjusted'] == -1 and data.at[i, 'RSI_highs_adjusted'] == 1:
                data.at[i, 'signal'] = 'Hidden Bearish Divergence'
    # data = data.drop(columns = ['close_highs','close_lows_adjusted','RSI','RSI_highs','RSI_lows'])
    # signal = data.loc[data['signal']!='']
    return data

