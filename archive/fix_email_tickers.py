import os

filepath = r'c:\Users\lokes\Downloads\project\sovereign-alpha\automation\email_digest.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace prediction ledger tickers
old_pred_tickers = "random.choice(['NVDA', 'AAPL', 'RELIANCE.NS', 'TCS.NS', 'BTC-USD'])"
new_pred_tickers = "random.choice(['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'BAJFINANCE.NS'])"
content = content.replace(old_pred_tickers, new_pred_tickers)

# Replace veto archive tickers
old_veto_tickers = "random.choice(['TSLA', 'GME', 'AMC', 'ZOMATO.NS', 'PAYTM.NS'])"
new_veto_tickers = "random.choice(['ZOMATO.NS', 'PAYTM.NS', 'NYKAA.NS', 'IDEA.NS', 'YESBANK.NS'])"
content = content.replace(old_veto_tickers, new_veto_tickers)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated email_digest.py")
