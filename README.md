# binance_delisting
Notifies about new delistings at Binance

# Run
Rename config.py.sample to config.py

Change config.py values

Sample crontab usage under non-root user "sammy":

```
crontab -e
```

```
*/30 * * * * cd /home/sammy/binance_delisting && python main.py
```
