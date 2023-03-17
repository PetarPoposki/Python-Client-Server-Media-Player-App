# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 23:07:47 2023

@author: HP
"""

import sys, socket, _thread, struct
import glob, os
import wave, pyaudio, pickle


song_directory = "songs"
pause_flag = False


def pause_unpause():
    global pause_flag
    pause_flag = not pause_flag


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
    songpath = os.path.join(song_directory,songname)
    wf = wave.open(songpath, 'rb')
    filesize = os.path.getsize(songpath)
    total_frames = wf.getnframes()
    p = pyaudio.PyAudio()
    # framerate can be different for different audio files, we have to send it to client
    rata = wf.getframerate()
    s.sendall(struct.pack("Q", rata))
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    input=True,
                    frames_per_buffer=CHUNK)        
    data = None
    datasent = 0
    # send total number of frames
    s.sendall(struct.pack("Q", total_frames))
    
    while filesize>datasent:
        if s:
            if not pause_flag:
                data = wf.readframes(CHUNK)
                datasent = datasent + len(data)
                a = pickle.dumps(data)
                message = struct.pack("Q",len(a))+a
                s.sendall(message)
    stream.stop_stream()
    stream.close()
    p.terminate()


def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message' % (len(data), length))
        data += more.decode()
    return data.encode()


l = _thread.allocate_lock()

    
def opsluzhiKlient(s):
    directory_path = "images"
    files = glob.glob(directory_path + '/*.png')

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
                        file_name = str(file).split("\\")[1]
                        filenames.append(file_name)
                 
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
                elif data[0] == "PAUSE":
                    pause_unpause()
            except struct.error:
                return
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('localhost', 10050))
s.listen(1)
print("Running")
while True:
    sc, sockname = s.accept()
    print(sockname)
    _thread.start_new_thread(opsluzhiKlient,(sc,))


    
