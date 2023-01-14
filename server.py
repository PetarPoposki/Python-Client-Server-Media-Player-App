# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 23:07:47 2023

@author: HP
"""

import sys, socket, _thread, struct
import glob, os
import wave, pyaudio, pickle


song_directory = "songs"
#songfilenames = glob.glob(song_directory + '/*.mp3')

def send_song(songname,s):
         
    print("SENDING NOW!")
    songpath = os.path.join(song_directory, songname)
    f = open(songpath, 'rb')
    size = os.path.getsize(songpath)
    song_size = struct.pack('!i', size)
    s.send(song_size)
    while size != 0:
        bytestosend = f.read(1024)
        size = size - len(bytestosend)
        s.send(bytestosend)
    print("SENT")
    #s.close()


def audio_stream(songname,s):
    CHUNK = 1024
    songpath = os.path.join(song_directory, songname)
    wf = wave.open(songpath, 'rb')
    
    p = pyaudio.PyAudio()
   
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    input=True,
                    frames_per_buffer=CHUNK)        
 
    data = None
    while True:
        if s:
            while True:
                data = wf.readframes(CHUNK)
                a = pickle.dumps(data)
                message = struct.pack("Q",len(a))+a
                s.sendall(message)
    stream.stop_stream()
    stream.close()
    p.terminate()
    #s.close()
    #s.shutdown(socket.SHUT_RDWR)


def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message' % (len(data), length))
        data += more.decode()
    return data.encode()


l = _thread.allocate_lock()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    
def opsluzhiKlient(s):
    
    #jpgfiles = glob.glob(directory_path+ '/*.jpg') problem mi pravese so jpg fajlovi
    directory_path = "images"
    files = glob.glob(directory_path + '/*.png')
    #print(files)

    filenames = []
    while True:
        if(s):
            try:
                length = struct.unpack("!i", s.recv(4))[0]
                data = (s.recv(length).decode()).split("|")
                if data[0] == 'HELLO':
                    msg = "CONFIRMED"
                    length = len(msg)
                    msg = struct.pack("!i", length) + msg.encode()
                    s.sendall(msg)
                    
                    for file in files:
                        #file_namelong = str(file).split("/")
                        #filename = file_namelong[1]
                        file_name = str(file).split("\\")[1]
                        filenames.append(file_name)
                  
                    #print(filenames)
                            
                        # Send the file name
                    msg = ""
                    for name in filenames:
                        if(msg == ""):
                            msg = name
                        else:
                            msg = msg + "|" + name
                            
                    print(msg)
                    length = len(msg)
                    msg = struct.pack("!i", length) + msg.encode()
                    s.sendall(msg)
                    
                    
                    for file in files:
                        with open(file, 'rb') as f:
                            image_data = f.read()
                            image_size = struct.pack('!i', len(image_data))
                            s.sendall(image_size + image_data)
                        f.close()
                elif data[0] == "PLAYSONG":
                    songname = data[1]
                    audio_stream(songname,s)
                elif data[0] == "DOWNLOAD":
                    songname = data[1]
                    send_song(songname,s)
            except struct.error:
                return
    
s.bind(('localhost', 10050))
s.listen(1)
print("Running")
while True:
    sc, sockname = s.accept()
    print(sockname)
    _thread.start_new_thread(opsluzhiKlient,(sc,))

    