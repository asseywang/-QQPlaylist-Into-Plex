import urllib
import requests
import http.client
import json
import sys
import urllib.request
import difflib
import re
import string
from urllib.parse import quote
from urllib.parse import urlencode
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from plexapi.myplex import MyPlexDevice
from plexapi.myplex import ResourceConnection

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'origin': 'https://y.qq.com',
    'referer': 'https://y.qq.com/portal/playlist.html',
    'Accept': 'application/json',
    'X-Plex-Token': 'YOUR_PLEX_TOKEN'  # 修改为你的有效 Plex Token
}

def fetch_url(url):
    try:
        r = requests.get(url, headers=headers)
        if r.status_code in [200, 201]:
            return r.json()
    except Exception as e:
        print(e)

def get_record(url):
    resp = urllib.request.urlopen(url)
    ele_json = json.loads(resp.read())
    return ele_json

def fetchPlexApi(path='', method='GET', getFormPlextv=False, token='YOUR_PLEX_TOKEN', params=None):
    headers = {'X-Plex-Token': token, 'Accept': 'application/json'}
    if getFormPlextv:
        url = 'plex.tv'        
        connection = http.client.HTTPSConnection(url)
    else:
        url = PLEX_URL.rstrip('/').replace('https://','')
        connection = http.client.HTTPSConnection(url)
    try:
        if method.upper() == 'GET':
            pass
        elif method.upper() == 'POST':
            headers.update({'Content-type': 'application/x-www-form-urlencoded'})
            pass
        elif method.upper() == 'PUT':
            pass
        elif method.upper() == 'DELETE':
            pass
        else:
            print("Invalid request method provided: {method}".format(method=method))
            connection.close()
            return

        connection.request(method.upper(), path , params, headers)     
        response = connection.getresponse()         
        r = response.read()             
        contentType = response.getheader('Content-Type')      
        status = response.status    
        connection.close()

        if response and len(r):     
            if 'application/json' in contentType:         
                return status, json.loads(r)
            elif 'application/xml' in contentType:
                return status, xmltodict.parse(r)
            else:
                return status, r
        else:
            return status, r

    except Exception as e:
        connection.close()
        print("Error fetching from Plex API: {err}".format(err=e))
        return None, None

def uniqify(seq):
    keys = {}
    for e in seq:
        keys[e] = 1
    return keys.keys()

def get_song_info(disstid):
    url = 'https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?'
    params = {
        'type': '1',
        'json': '1',
        'utf8': '1',
        'onlysong': '0',
        'disstid': disstid,
        'g_tk': '5381',
        'loginUin': '0',
        'hostUin': '0',
        'format': 'json',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq.json',
        'needNewCode': '0',
    }
    url += urlencode(params)
    result = fetch_url(url)
    dissname = result['cdlist'][0]['dissname']
    dissdesc = result['cdlist'][0]['desc']
    songlist = result['cdlist'][0]['songlist']
    for song in songlist:
        strMediaMid = song['strMediaMid']
        songMid = song['songmid']
        songname = song['songname']
        singer = song['singer'][0]['name']
        albumname=song['albumname']
        print(albumname)
        yield strMediaMid, songMid, songname, singer,albumname, dissname, dissdesc

def getqqmusiclist(dissid):
    song_list = []
    playlist_info = {}

    for item in get_song_info(dissid):
        song_list1= {}
        strMediaMid, songMid, songname,singer,albumname, dissname, dissdesc= item
        singer = singer
        pattern = re.compile(r'[\\/:：*?"<>|\r\n]+')
        songname = re.sub(pattern, " ", songname)
        dissname = re.sub(pattern, " ", dissname)
        albumname = re.sub(pattern, " ", albumname)
        song_list1.update(name = songname,singername = singer,albumname=albumname)
        song_list.append(song_list1)
    playlist_info.update(name = dissname,summary =dissdesc,songlist = song_list )
    return(playlist_info) 
    
if __name__ == '__main__':
    PLEX_URL = 'https://YOUR_PLEX_URL'
    PLEX_TOKEN = 'YOUR_PLEX_TOKEN'
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    machineId = plex.machineIdentifier
    playlist_source = '2'
    PLAYLIST_ID = '8738928174'     #QQ歌单
    if_new_playlist = '2'
    if if_new_playlist == '1' :
        for playlist in plex.playlists():
            print(playlist)
        local_playlist_id = '111743'

    track_id = []
    tracks_unfound = []
    tracks_added = []
    isfirstmatch = False
    if if_new_playlist == '2':
        isfirstmatch = True

    if playlist_source == '2' :
        songs = getqqmusiclist(PLAYLIST_ID)
        playlist_title = songs['name'].replace(" ", "")
        # try:
        #     playlist_summary = songs['summary'].replace("\n", ",").replace(" ", ",")
        # except:
        #     pass       
        print(playlist_title)
        # print(playlist_summary)
        for song in songs['songlist'] :
                # song_name = re.sub(u"\\(.*?\\)|\\（.*?）|\\[.*?]", "", song['name']) 
                song_name = song['name']
                print("歌单的歌曲名称："+song_name)
                
                if plex.search(song_name):
                    ismatch = False
                    for localsong in plex.search(song_name):
                        if localsong.type == 'track' :
                            print("Plex媒体")
                            print(localsong.title)
                            song_score = 0
                            artist_score = 0
                            album_score = 0
                            song_score = difflib.SequenceMatcher(None, song_name, localsong.title).quick_ratio() * 100
                            album_score = difflib.SequenceMatcher(None, song['albumname'], localsong.parentTitle).quick_ratio() * 100
                            artist_score = difflib.SequenceMatcher(None, song['singername'], localsong.grandparentTitle).quick_ratio() * 100
                            total_score =  (song_score + artist_score + album_score ) / 3
                            if total_score > 33 :
                                ismatch = True
                                if isfirstmatch :
                                    url1 = '/playlists?uri=server%3A%2F%2F' + machineId + '%2Fcom.plexapp.plugins.library%2Flibrary%2Fmetadata%2F' + str(localsong.ratingKey) + '&includeExternalMedia=1&title=' + playlist_title + '&smart=0&type=audio&'
                                    url2 = quote(url1,safe=string.printable)
                                    print(url2)
                                    status, data = fetchPlexApi(url2,"POST",token=PLEX_TOKEN)
                                    print(data)
                                    tracks_added.append(song_name + ' -- ' + song['singername'])
                                    local_playlist_id = data['MediaContainer']['Metadata'][0]['ratingKey']
                                    try:
                                        data1 = fetchPlexApi(quote('/playlists/'+ local_playlist_id +'?includeExternalMedia=1&summary=' + playlist_summary + '&',safe=string.printable),"PUT",token=PLEX_TOKEN)
                                    except:
                                        pass
                                    isfirstmatch = False
                                    break
                                tracks_added.append(song_name + ' -- ' + song['singername'])
                                print(localsong.ratingKey)
                                data = fetchPlexApi('/playlists/'+ local_playlist_id + '/items?uri=server%3A%2F%2F' + machineId + '%2Fcom.plexapp.plugins.library%2Flibrary%2Fmetadata%2F' + str(localsong.ratingKey) + '&includeExternalMedia=1&',"PUT",token=PLEX_TOKEN)
                                break
                    if not ismatch :
                        tracks_unfound.append(song['name'] + ' -- ' + song['singername'])                                        
                else:
                    tracks_unfound.append(song['name'] + ' -- ' + song['singername'])

    print('以下歌曲没有在媒体库中找到')
    print(tracks_unfound)
    print(len(tracks_unfound))
    print('以下歌曲已经添加到歌单')
    print(tracks_added)
    print(len(tracks_added))
