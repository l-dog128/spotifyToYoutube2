from dotenv import load_dotenv
import os
import base64
from requests import post,get
import json
import questionary
from pytube import YouTube
from progress.bar import Bar

# general stuff
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
username = ""

yt_KEY = os.getenv("API_KEY")

#spotify stuff
def get_token():
    auth_string = client_id +":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes),"utf-8")

    url  = "https://accounts.spotify.com/api/token"
    headers ={
        "Authorization":"Basic " + auth_base64,
        "Content-Type" :"application/x-www-form-urlencoded"
    }

    data ={"grant_type":"client_credentials"}
    result = post(url,headers=headers,data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return{"Authorization":"Bearer " + token}

def search_for_artist(token,artist_name):
    url ="https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url,headers=headers)
    json_result = json.loads(result.content)
    print(json_result)

def get_user_playlists_link(token,username):
    url = f"https://api.spotify.com/v1/users/{username}/playlists"
    headers = get_auth_header(token)
    
    query = "?limit=20"

    query_url = url + query
    result = get(query_url,headers=headers)
    json_result = json.loads(result.content)["items"]
    
    return json_result
def clean_tracks_from_playlist(json_result):
    tracks = {}
    for result in json_result:
        tracks.update({result["track"]["name"]:result["track"]["artists"][0]["name"]})
    return tracks

def get_tracks_from_playlist(token,username):
    
    # if user name is none get user to input userName
    if username == "":
        username = input("Username ")
    
    playlist_link = get_user_playlists_link(token,username)
    # choose playlist
    names_links =clean_API_response(playlist_link)
    playlist_name=questionary.select(
        "pick a playlist to copy",
        choices=list(names_links.keys())
    ).ask()
    playlist_link =names_links[playlist_name]


    # TODO: add stuff if playlist is too long
    # 
    headers = get_auth_header(token)
    query = '?market=GB&fields=tracks%28items%28track%28name%2Cartists%28name%29%29%29%29'
    query_url = playlist_link + query
    result = get(query_url,headers=headers)
    
    json_result = json.loads(result.content)["tracks"]["items"]
    return clean_tracks_from_playlist(json_result)

def clean_API_response(json_result):
    names_links = {}
    for result in json_result:
        names_links.update({result["name"]:result["href"]})
    return names_links

# YT Stuff

def get_yt_link(query):
    url = f"https://www.googleapis.com/youtube/v3/search?key={yt_KEY}&q={query}&type=video&part=snippet&maxResults=1"
    result = get(url)
    yt_link = "https://www.youtube.com/watch?v="
    return yt_link + json.loads(result.content)["items"][0]["id"]["videoId"]


#Audio download bit
def download_yt_audio(yt_link):
    yt=YouTube(yt_link,
        use_oauth=True,
        allow_oauth_cache=True)
    # want itag 140 just for 128kbps audio 
    stream =yt.streams.get_by_itag(140)
    
    stream.download()
    

#main
def __main__():
    #spotify bit and playlist selection
    # TODO maybe add username selection
    
    token = get_token()
    songs_dict = get_tracks_from_playlist(token,username)

    #TODO remove so shit doesn't fill up
    yt_links = []
    for song in songs_dict:
        yt_links.append(get_yt_link(song +" "+ songs_dict.get(song)))

    #yt_links = ['https://www.youtube.com/watch?v=UtF6Jej8yb4', 'https://www.youtube.com/watch?v=w869Avr_fXI', 'https://www.youtube.com/watch?v=v7Rf9bopNmk', 'https://www.youtube.com/watch?v=vn-6fiVkAcA', 'https://www.youtube.com/watch?v=Y66j_BUCBMY', 'https://www.youtube.com/watch?v=Va75GaPv5jY', 'https://www.youtube.com/watch?v=XUd2S8a2ChQ', 'https://www.youtube.com/watch?v=nWyhUoxAbYI', 'https://www.youtube.com/watch?v=fe4EK4HSPkI', 'https://www.youtube.com/watch?v=e8xni3EcIbc', 'https://www.youtube.com/watch?v=6ECw5DTULQ8', 'https://www.youtube.com/watch?v=CfihYWRWRTQ', 'https://www.youtube.com/watch?v=IyVPyKrx0Xo', 'https://www.youtube.com/watch?v=BcsfftwLUf0', 'https://www.youtube.com/watch?v=Hy_xJRbTq2Q', 'https://www.youtube.com/watch?v=SSbBvKaM6sk', 'https://www.youtube.com/watch?v=1prhCWO_518', 'https://www.youtube.com/watch?v=3G5F4QDoIXo', 'https://www.youtube.com/watch?v=WBtVjjLtEY8', 'https://www.youtube.com/watch?v=Hxm4Ft1ZgLA', 'https://www.youtube.com/watch?v=TBC77x59-BY'] 

    os.chdir("output")

    bar = Bar("Downloading",max=len(yt_links))
    for link in yt_links:
        try:
            download_yt_audio(link)
        except:
            print("failed to download",link)
        bar.next()
            
    bar.finish()

if __main__:
    __main__()
