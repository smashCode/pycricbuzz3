import requests
import json
import sys
from bs4 import BeautifulSoup
from time import sleep
import subprocess as s 
#from pycricbuzz import Cricbuzz
#c=Cricbuzz()
#c.start()

class Cricbuzz():
	url = "http://synd.cricbuzz.com/j2me/1.0/livematches.xml"
	def start(self):
		choice=input("Please enter your choice\n1. View All matches")
		#print("your choice "+choice)
		data=self.matches()
		#print(data)
		self.parseMatches(data)
		for i in range(0,5):
			choice= input("enter id followed by descriptid with space\n1 for commentary\n2 for score card\n example 1 2 for match id 1 and live score")
			choice=choice.split(" ")
			if choice[1]=='1':
				while(True):
					data=self.commentary(int(choice[0]))
					self.parseCommentary(data)
					#print(data)
					sleep(30)		
			elif choice[1]=='2':
				while(True):				
					data=self.scorecard(int(choice[0]))
					#print(data)
					self.parseScorecard(data)
					sleep(120)

	def parseCommentary(self,data):
		print("Match Status\n"+data['matchinfo']['status'])
		print("\n"+data['matchinfo']['mchstate'])
		print("\n"+data['commentary'][0])
		s.call(['notify-send',"Live commentary",data['commentary'][0]])

	def parseScorecard(self,data):
		print("Squad of "+data['squad'][0]['team']+"\n\n")
		
		for member in data['squad'][0]['members']:
			print(member)
		
		print("Squad of "+data['squad'][1]['team']+"\n\n")
		for member in data['squad'][1]['members']:
			print(member)
		print(data['matchinfo']['status'])
		
		for innings in data['scorecard']:
			print("score card\n"+innings['inngdesc'])
			text=innings['batteam']+" scored "+innings['runs']+"/"+innings['wickets']+"  in "+innings['overs']+" overs against "+innings['bowlteam']
			
			s.call(['notify-send',"current score",text])

			print(text)
			
			print("Batting\n")
			for batsman in innings['batcard']:
				print(batsman['name']+"\t runs:"+batsman['runs']+" balls:"+batsman['balls']+" sixes:"+batsman['six']+" fours:"+batsman['fours'])
				if batsman['dismissal']:
					print(batsman['dismissal']+"\n")
			
			print("bowling card")
			for bowler in innings['bowlcard']:
				print(bowler['name']+"\t runs:"+bowler['runs']+" maidens:"+bowler['maidens']+" wickets:"+bowler['wickets']+" overs:"+bowler['overs'])
				

	def parseMatches(self,data):
		#matches=json.loads(data)
		for match in data:
			print("ID:"+match['id']+"."+match['srs']+" \n\tstatus"+match['status'])		
	
	def __init__(self):
		pass

	def getxml(self,url):
		try:
			r = requests.get(url)
		except requests.exceptions.RequestException as e: 
			print(e)
			sys.exit(1)
		soup = BeautifulSoup(r.text,"html.parser")
		return soup

	def matchinfo(self,match):
		d = {}
		d['id'] = match['id']
		d['srs'] = match['srs']
		d['mchdesc'] = match['mchdesc']
		d['mnum'] = match['mnum']
		d['type'] = match['type']
		d['mchstate'] = match.state['mchstate']
		d['status'] = match.state['status']
		return d

	def matches(self):
		xml = self.getxml(self.url)
		matches = xml.find_all('match')
		info = []
		
		for match in matches:
			info.append(self.matchinfo(match))
		return info

	def livescore(self,mid):
		xml = self.getxml(self.url)
		match = xml.find(id = mid)
		if match is None:
			return "Invalid match id"
		if match.state['mchstate'] == 'nextlive':
			return "match not started yet"
		curl = match['datapath'] + "commentary.xml"
		comm = self.getxml(curl)
		mscr = comm.find('mscr')
		batting = mscr.find('bttm')
		bowling = mscr.find('blgtm')
		batsman = mscr.find_all('btsmn')
		bowler= mscr.find_all('blrs')
		data = {}
		d = {}
		data['matchinfo'] = self.matchinfo(match)
		d['team'] = batting['sname']
		d['score'] = []
		d['batsman'] = []
		for player in batsman:
			d['batsman'].append({'name':player['sname'],'runs': player['r'],'balls':player['b'],'fours':player['frs'],'six':player['sxs']})
		binngs = batting.find_all('inngs')
		for inng in binngs:
			d['score'].append({'desc':inng['desc'], 'runs': inng['r'],'wickets':inng['wkts'],'overs':inng['ovrs']})
		data['batting'] = d
		d = {}
		d['team'] = bowling['sname']
		d['score'] = []
		d['bowler'] = []
		for player in bowler:
			d['bowler'].append({'name':player['sname'],'overs':player['ovrs'],'maidens':player['mdns'],'runs':player['r'],'wickets':player['wkts']})
		bwinngs = bowling.find_all('inngs')
		for inng in bwinngs:
			d['score'].append({'desc':inng['desc'], 'runs': inng['r'],'wickets':inng['wkts'],'overs':inng['ovrs']})
		data['bowling'] = d
		return data

	def commentary(self,mid):
		xml = self.getxml(self.url)
		match = xml.find(id = mid)
		if match is None:
			return "Invalid match id"
		if match.state['mchstate'] == 'nextlive':
			return "match not started yet"
		curl = match['datapath'] + "commentary.xml"
		comm = self.getxml(curl).find_all('c')
		d = []
		for c in comm:
			d.append(c.text)
		data = {}
		data['matchinfo'] = self.matchinfo(match)
		data['commentary'] = d
		return data 

	def scorecard(self,mid):
		xml = self.getxml(self.url)
		match = xml.find(id = mid)
		if match is None:
			return "Invalid match id"
		if match.state['mchstate'] == 'nextlive':
			return "match not started yet"
		surl = match['datapath'] + "scorecard.xml"
		scard = self.getxml(surl)
		scrs = scard.find('scrs')
		innings = scrs.find_all('inngs')
		data = {}
		data['matchinfo'] = self.matchinfo(match)
		squads = scard.find('squads')
		teams = squads.find_all('team')
		sq = []
		sqd = {}

		for team in teams:
			sqd['team'] = team['name']
			sqd['members'] = []
			members = team['mem'].split(", ")
			for mem in members:
				sqd['members'].append(mem)
			sq.append(sqd.copy())
		data['squad'] = sq	
		d = []
		card = {}
		for inng in innings:
			bat = inng.find('bttm')
			card['batteam'] = bat['sname']
			card['runs'] = inng['r']
			card['wickets'] = inng['wkts']
			card['overs'] = inng['noofovers']
			card['runrate'] = bat['rr']
			card['inngdesc'] = inng['desc']
			batplayers = bat.find_all('plyr')
			batsman = []
			bowlers = []
			for player in batplayers:
				status = player.find('status').text
				batsman.append({'name':player['sname'],'runs': player['r'],'balls':player['b'],'fours':player['frs'],'six':player['six'],'dismissal':status})
			card['batcard'] = batsman
			bowl = inng.find('bltm')
			card['bowlteam'] = bowl['sname']
			bowlplayers = bowl.find_all('plyr')
			for player in bowlplayers:
				bowlers.append({'name':player['sname'],'overs':player['ovrs'],'maidens':player['mdns'],'runs':player['roff'],'wickets':player['wkts']})
			card['bowlcard'] = bowlers
			d.append(card.copy())
		data['scorecard'] = d
		return data
		


