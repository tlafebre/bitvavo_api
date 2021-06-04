#!/usr/bin/env python3

# graphs
# x ago

import os

from collections import namedtuple
from functools import reduce

import pandas as pd

from python_bitvavo_api.bitvavo import Bitvavo

DEFAULT_CURRENCY = "EUR"

bitvavo = Bitvavo({
  "APIKEY": os.environ["BITVAVOKEY"],
  "APISECRET": os.environ["BITVAVOSECRET"],
  "RESTURL": "https://api.bitvavo.com/v2",
  "WSURL": "wss://ws.bitvavo.com/v2/",
  "ACCESSWINDOW": 10000,
  "DEBUGGING": False
})

Trade        = namedtuple("Trade", "amount price side")
BalanceEntry = namedtuple("BalanceEntry", "symbol available in_order")

market        = lambda s: "{}-{}".format(s, DEFAULT_CURRENCY)
owned_symbols = lambda  : (e.symbol for e in balance() if e.symbol != DEFAULT_CURRENCY)
percentage    = lambda s: "{0:.2f}%".format(s)

def balance():
  return (BalanceEntry(e["symbol"], float(e["available"]), e["inOrder"]) for e in bitvavo.balance({}))

def get_trades(symbol):
  return (Trade(float(t["amount"]), float(t["price"]), t["side"]) for t in bitvavo.trades(market(symbol), {}))

def subtotal(trades):
  return sum(-x.amount * x.price if x.side == "sell" else x.amount * x.price for x in trades)

def symbol_balance_entry(symbol):
  return next(filter(lambda e: e.symbol == symbol, balance()), None)

def get_ticker_price(symbol):
  return float(bitvavo.tickerPrice({"market": market(symbol)}).get("price", 0))

def get_total_invested(symbol):
  return subtotal(get_trades(symbol)) 

def get_current_value(symbol):
  sd = list(filter(lambda e: e.symbol == symbol, balance()))
  return 0.0 if len(sd) != 1 else sd[0].available * get_ticker_price(symbol)

def summary_line(symbol):
  ent = symbol_balance_entry(symbol)

  amt = ent.available
  tot = round(get_total_invested(symbol), 2)
  avg = tot / amt
  pri = get_ticker_price(symbol)
  val = round(get_current_value(symbol), 2)
  yld = round((val - tot), 2)
  ypt = percentage((val - tot) / tot * 100)

  return [tot, amt, avg, pri, val, yld, ypt]

def overview():
  symbols = list(owned_symbols())
  columns = ["TotInvested", "Amount", "AvgBuyPrice", "CurPrice", "Value", "Yield", "YieldPct"]
  rows    = [summary_line(symbol) for symbol in symbols]
  sdf = pd.DataFrame(
          rows,
          index=symbols,
          columns=columns
  )

  total = [
    sdf.TotInvested.sum(), 
    "-", 
    "-", 
    "-", 
    sdf.Value.sum(), 
    sdf.Yield.sum(), 
    percentage((sdf.Yield.sum() / sdf.Value.sum()) * 100)
  ]

  sdf.loc["Total"] = total

  print(sdf)

if __name__ == "__main__":
  overview()
