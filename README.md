# binance_delisting
Notifies about new delistings at Binance

# Run
Sample crontab usage under non-root user "sammy":

```
crontab -e
```

```
*/30 * * * * cd /home/sammy/binance_delisting && python main.py
```
