<div align="center">

<h1>HexCoin</h1>

<p>
  A Telegram economy bot written in Python.
</p>

<p>
  It gives users a wallet, lets them earn HexCoins, transfer them to other users,
  and generally pretend the numbers in MongoDB are worth something.
</p>

<p>
  Built with <strong>Pyrogram + MongoDB</strong>.
</p>

</div>

<hr>

<h2>What it does</h2>

<pre>
/start       → create wallet
/balance     → check balance
/daily       → collect daily reward
/send 100    → send 100 coins (reply to a user)
/stats       → see the state of the economy
/id          → get Telegram ID
/help        → commands
/broadcast   → owner only
</pre>

<p>
New wallets start with <strong>100 HexCoins</strong>.
</p>

<p>
<code>/daily</code> gives <strong>100 HexCoins every 24 hours</strong>.
</p>

<p>
Transfers are atomic, so two requests can't casually spend the same balance at the same time.
</p>

<h2>Stack</h2>

<pre>
Python
Pyrogram
PyMongo
MongoDB
asyncio
</pre>

<h2>Setup</h2>

<pre>
git clone https://github.com/amanuh/HexCoin-Bot.git
cd HexCoin-Bot

pip install pyrogram tgcrypto pymongo pytz
python bot.py
</pre>

<p>Put your credentials in <code>bot.py</code>:</p>

<pre>
api_id = 'your_api_id'
api_hash = 'your_api_hash'
bot_token = 'bot_token'

OWNER_ID = 293768732
CHAT_GROUP_ID = -123456788
</pre>

<p>And your MongoDB URI:</p>

<pre>
mongo_uri = "mongodb+srv://username:password@..."
</pre>

<p>The bot creates this automatically:</p>

<pre>
hexcoin_bot
└── users
    ├── _id
    ├── balance
    └── last_claim
</pre>

<h2>The economy</h2>

<p>
HexCoin is an application-level currency.
The database is the ledger and the bot is the authority.
</p>

<p>
If the database says you have <code>500 HexCoins</code>, you have <code>500 HexCoins</code>.
</p>

<p>
If the database says you have <code>0</code>, congratulations.
</p>

<h2>Notes</h2>


<p>Logs go to:</p>

<pre>
hexcoin_bot.log
</pre>

<hr>

<div align="center">

<strong>HexCoin</strong>

<br>

<sub>its completely imaginary money .</sub>

</div>
