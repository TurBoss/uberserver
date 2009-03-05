import sqlalchemy, time, sys

if not len(sys.argv) == 3:
	print 'usage: migrate.py [/path/to/accounts.txt] [dburl]'
	sys.exit()

print
print 'starting migration'
print

accountstxt = sys.argv[1]
dburl = sys.argv[2]

def _bin2dec(s): return int(s, 2)

print 'opening database'
engine = sqlalchemy.create_engine(dburl, pool_size=512, pool_recycle=300)
UsersHandler = __import__('SQLUsers').UsersHandler
db = UsersHandler(None, engine)

print 'reading accounts'

f = open(accountstxt, 'r')
data = f.read()

f.close()
print 'scanning accounts'
accounts = {}

for line in data.split('\n'):
	if line:
		line = line.split()
		if len(line) < 8: continue

		username = line[0]
		password = line[1]
		access = line[2]
		uid = line[3]
		lastlogin = int(line[4])/1000
		ip = line[5]
		dunno = line[6]
		country = line[7]
		mapgrades = ' '.join(line[8:])

		accss = _bin2dec(access)
		ingame = _bin2dec(access[-23:21])
		if accss & 16777216: bot = True
		else: bot = False
		if bot: ingame = ingame*2

		if accss & 3: access = 'admin'
		elif accss & 2: access = 'mod'
		else: access = 'user'
		accounts[username] = {'user':username, 'pass':password, 'ingame':ingame, 'lastlogin':lastlogin, 'uid':uid, 'ip':ip, 'country':country, 'bot':bot, 'mapgrades':mapgrades, 'access':access}

print
print 'writing accounts to database'
db.inject_users(accounts.values())