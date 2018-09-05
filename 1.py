import json
import time
import threading
import os
from functools import reduce
platform_ids = ['NA1','OC1','OC','NA','KR','EUW','EUW1','EUNE','EUNE1']
rate = 20

class Watch :
        def __init__(self):
                self.value = False
        def __eq__(self, other):
                return self.value == other
        def stop (self):
                self.value = True
                return self
def get_history (lower_bound,player_id,platform_id):
        import requests
        l = 'https://acs.leagueoflegends.com/v1/stats/player_history/{}/{}?begIndex={}&endIndex={}&'.format(platform_id,player_id,lower_bound,lower_bound+rate)
        d = None
        while True:
                d = json.loads(requests.get(l).text)
                if d == {"httpStatus": 429, "errorCode": "CLIENT_RATE_LIMITED"}: continue
                break
        return [(game['gameId'], game['platformId']) for game in d['games']['games']]
def get_matches_info (match_id,pid):
        import requests
        d = None
        l = 'https://acs.leagueoflegends.com/v1/stats/game/{}/{}'.format(pid,match_id)
        while True:
                d = json.loads(requests.get(l).text)
                if d == {"httpStatus": 429, "errorCode": "CLIENT_RATE_LIMITED"}: continue
                break
        return d
def get_account_id(summoner,region):
        import requests
        while True:
                l = 'https://acs.leagueoflegends.com/v1/players?name={}&region={}'.format(summoner,region)
                d = json.loads(requests.get(l).text)
                if d == {"httpStatus": 429, "errorCode": "CLIENT_RATE_LIMITED"}: continue
                break
        return d['accountId']
def get_platform_id(summoner,region):
        import requests
        while True:
                l = 'https://acs.leagueoflegends.com/v1/players?name={}&region={}'.format(summoner,region)
                d = json.loads(requests.get(l).text)
                if d == {"httpStatus": 429, "errorCode": "CLIENT_RATE_LIMITED"}: continue
                break
        return d['platformId']
def get_all_summoners_old(data):
        return ([(players['player']['summonerName'],players['player']['platformId']) for players in data['participantIdentities']])
def get_all_summoners(data):
        return ([(players['player']['summonerName'],players['player']['accountId']) for players in data['participantIdentities']])
def load_page (pages,page,summoner_id,platform_id,s,sw):
        match = []
        while True:
                try:
                        match = get_history(page*rate, summoner_id,platform_id)
                        break
                except:
                        time.sleep(0.01)
        if match == []: sw.stop()
        else:pages[page] = match
        s.release()
        
def load_match_history (match_infos,match_id,s,matches_in_storage,platform_id):
        try:
                if match_id in matches_in_storage or os.path.exists(os.path.join("Match_Infos",platform_id,str(match_id))):
                        match_infos[str(match_id)+platform_id] = read_match_info(match_id,platform_id)
                        matches_in_storage[platform_id].add(match_id)
                        s.release()
                        return
        except: pass
        while True:
                try:
                        data = get_matches_info(match_id,platform_id)
                        break
                except:
                        time.sleep(0.005)

        matches_in_storage[platform_id].add(match_id)
        match_infos[str(match_id)+platform_id] = data
        write_match_info(data,match_id,platform_id)
        s.release()
        
def update_match_list(existing_list,summoner_id,platform_id):
        page = 0
        new_match_found = False
        while True:
            while True:
                    try:
                            matches = get_history(page*rate, summoner_id,platform_id)
                            break
                    except:
                            time.sleep(0.01)
                
            page +=1
            if matches == []: break
            for match,mpid in (reversed(sorted(matches))):
                if [match,mpid] in existing_list:
                    return new_match_found
                else:
                        new_match_found = True
                existing_list.append((match,mpid))
        return new_match_found
class DataParser :
        def __init__(self,sn,rg):
                self.summoner_name = sn
                self.summoners = dict()
                self.stored_match_infos = dict()
                for platform in platform_ids:
                        self.stored_match_infos[platform] = set()
                        try: self.stored_match_infos[platform] = set(read_index(platform))
                        except: pass
                try:
                        self.summoner_id = get_account_id(sn,rg)
                        self.platform_id = get_platform_id(sn,rg)
                        print ("Summoner Name : {}".format(sn))
                        print ("Summoner ID :{}, Platform ID: {}".format(self.summoner_id,self.platform_id))
                except:
                        print ('Player not found')
                        raise
        def mainloop(self):
                self.run()
      
        def run (self):
                self.pages = dict()
                self.match_infos = dict()
                self.summoners = dict()
                self.summoner_names = dict()
                page = 0
                t = []
                semaphore = threading.BoundedSemaphore(20)
                stop_watch = Watch()
                match_history_loaded = False # look for player's match history locally
                try:
                        self.full_match_history = read_match_history_list(self.summoner_id,self.platform_id)
                        match_history_loaded = True
                        print ("Match History Loaded: {}".format(match_history_loaded))
                        new_match_found = update_match_list(self.full_match_history,self.summoner_id,self.platform_id)    # look for new matches
                        print ("New match found: {}".format(new_match_found))
                        
                        if new_match_found:
                                write_match_history_list(self.full_match_history,self.summoner_id,self.platform_id)
                except :
                        print ("Match History Loaded: {}".format(match_history_loaded))
 
                if match_history_loaded == False : 
                        print ("Downloading match history list...")
                        while  stop_watch != True:
                                semaphore.acquire()
                                t.append(threading.Thread(target=load_page,
                                                          args=(self.pages,page,self.summoner_id,self.platform_id,semaphore,stop_watch)))
                                t[page].start()
                                page+=1
                                
                        # Wait for all Thread to terminate #
                        for aThread in t:
                                aThread.join()
                        
                        self.full_match_history = pages_to_list(self.pages)
                        write_match_history_list(self.full_match_history,self.summoner_id,self.platform_id)
                
                semaphore = threading.BoundedSemaphore(20)
                t = []
                
                print ("There are {} matches".format(len(self.full_match_history)))
                print ("Loading match history ...")
                
                for i in range(0,len(self.full_match_history)):
                        match_id,match_pid  = self.full_match_history[i]
                        semaphore.acquire()
                        t.append(threading.Thread(target=load_match_history,
                                                      args=(self.match_infos,match_id,semaphore,self.stored_match_infos,match_pid)))
                        t[i].start()
                for aThread in t:
                        aThread.join()
                # Write index file #
                t_sc = self.stored_match_infos
                for platform_id in self.stored_match_infos.keys():
                        write_index(list(t_sc[platform_id]),platform_id)

                print ("Processing data ...")
                ###

                for match_id,mpid in self.full_match_history:
                        #print (match_id, mpid)
                        k = str(match_id) + mpid
                        summoners_ingame = get_all_summoners(self.match_infos[k])
                        
                        for summonerName,accountId in summoners_ingame:
                                if accountId == 0: continue
                                try:
                                        self.summoners[accountId].append((match_id,mpid))
                                except:
                                        self.summoners[accountId] = [(match_id,mpid)]
                                try:
                                        self.summoner_names[accountId].add(summonerName)
                                except:
                                        self.summoner_names[accountId] = set([summonerName])
                                #print ("||", summonerName, "||")
                                
                
                write_every_single_thing_new(self.summoners,self.summoner_name,len(self.full_match_history),self.summoner_names,self.platform_id)
                
def write_every_single_thing_new (ddd,name,N,summoner_names,pid):
        if os.path.exists("results") == False: os.mkdir("results")
        if os.path.exists(os.path.join("results",pid)) == False: os.mkdir(os.path.join("results",pid))

        fname = os.path.join("results",pid,name+'.txt')
        print ('Writing {}'.format(fname))
        
        f = open (fname,'w')
        f.write("-"*20+"\n")
        f.write("-"*20+"\n")
        f.write("There are a total of {} matches read\n".format(N))
        f.write("-"*20+"\n")
        d = dd = ddd
        j = dict([(len(v),[]) for v in d.values()]) # sort number of match played toggether
        #print ([a for a in d.values()])
        for sm in d:
                j[len(d[sm])].append(sm)
        # encoding problems (TODO)
        
        player_id = dict()
        for v in reversed(sorted(j.keys())):
                sout = ""
                for sid in j[v]:
                        names = reduce((lambda n, nn: n + "," + nn ) , list(summoner_names[sid]))
                        player_id [sid] = "Account ID: {0: <11}".format(sid) + "Summoner Name: {}".format(names)
                        try:
                                f.write ("{}:{}\n".format(player_id[sid],v))
                        except:
                                f.write ("{}:{}\n".format(player_id[sid].encode("utf-8"),v))
        f.write("\n"+"-"*10+"%MID%"+"-"*10+"\n")
        for sid in sorted(dd.keys()):
                try:
                        f.write ("{}\n".format(player_id[sid]))
                except:
                        f.write ("{}\n".format(player_id[sid].encode("utf-8")))
                for m,r in sorted(dd[sid]):
                        f.write("https://matchhistory.na.leagueoflegends.com/en/#match-details/{}/{}?tab=overview\n".format(r,m))
                f.write('\n')
        f.close()
def pages_to_list (pages):
        l = []
        for page in range(0,1+max(pages.keys())):
                for match in pages[page]:
                        l.append(match)
        return l 
def write_match_info(match_info,match_id,platform_id):
        with open(os.path.join("Match_Infos",platform_id,str(match_id)), 'w') as f:
                json.dump(match_info, f)
                f.close()
def read_match_info(match_id,platform_id):
        with open(os.path.join("Match_Infos",platform_id,str(match_id)),'r') as f:
                k = json.load(f)
                f.close()
                return k
# matches list #
def write_index(match_ids,platform_id):
        with open(os.path.join("Match_Infos",platform_id,"index.json"),'w') as f:
                json.dump(match_ids, f)
                f.close()
def read_index(platform_id):
        with open(os.path.join("Match_Infos",platform_id,"index.json"),'r') as f:
                k = json.load(f)
                f.close()
                return k
def write_match_history_list(match_list,summoner_id,platform_id):
        with open(os.path.join("Match_List",platform_id,str(summoner_id)),'w') as f:
                json.dump(match_list, f)
        f.close()
def read_match_history_list(summoner_id,platform_id):
        with open(os.path.join("Match_List",platform_id,str(summoner_id)),'r') as f:
                t = json.load(f)
        f.close()
        return t
def make_folders ():
        if not(os.path.lexists("Match_Infos")) : os.makedirs("Match_Infos")
        if not(os.path.lexists("Match_List")) : os.makedirs("Match_List")
        for pid in platform_ids:
                p = os.path.join("Match_List",pid)
                p1 = os.path.join("Match_Infos",pid)
                if not(os.path.exists(p)): os.mkdir (p)
                if not(os.path.exists(p1)): os.mkdir (p1)
if __name__ == "__main__":
        #apple OCE
        make_folders()
        #D = DataParser('yournewmom','NA1')
        D = DataParser('A Cute Cat Irl','NA1')
        D.mainloop()
