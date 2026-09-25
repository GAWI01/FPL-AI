import argparse
import pandas as pd
from .engine import BacktestConfig, BacktestEngine

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("historical_csv")
    parser.add_argument("--start-gw",type=int,default=1)
    parser.add_argument("--end-gw",type=int)
    parser.parse_args()
    raise SystemExit("Use BacktestEngine with the project's prediction adapter; no alternate model is silently substituted.")

if __name__=="__main__": main()
