# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 23:17:05 2023
@author: HP
"""


from tkinter import ttk
import os
import sys, socket, _thread, struct
import pyaudio, pickle
import tkinter as tk

root = tk.Tk()
root.title('MP3 Player')
root.iconbitmap("clientimages/gui.ico")

N = 0

l = _thread.allocate_lock()
imagenames = []
t = 0

stream = None
play_flag = []
pause_flag = []

def download_song(i):
    name = imagenames[i].split(".")[0] + ".wav"
    clientsongs = "clientsongs"
    songpath = os.path.join(clientsongs, name)
    if os.path.exists(songpath):
        print(name + " is already downloaded.")
    else:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s2.connect(('localhost', 10050))
        msg = "DOWNLOAD|" + imagenames[i].split(".")[0] + ".wav"
        length = len(msg)
        print(msg)
        fullmsg = (struct.pack("!i", length)).decode() + msg
        
        # create a new ttk.Progressbar widget
        progress = ttk.Progressbar(root, orient="horizontal",
                                   length=200, mode="determinate")
        progress.grid(row=N+1, column=3)
        # create a label widget
        song_name_label = tk.Label(root, text=name)
        
        song_name_label.grid(row=N+1, column=4)
        s2.sendall(fullmsg.encode())
        simni(s2,i,progress,song_name_label)
        
    
def falseflag(i):
    global play_flag
    play_flag[i] = False
    
def pause_unpause(i):
    global pause_flag
    global play_flag
    if(play_flag[i] == True):
        s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s3.connect(('localhost', 10050))
        msg = "PAUSE|SONG"
        fullmsg = (struct.pack("!i", length)) + msg.encode()
        s3.sendall(fullmsg)
        pause_flag[i] = not pause_flag[i]
        s3.close()
    else:
        print("That song is not playing.")


def song_request(i):
    global play_flag
    k = 0
    for j in range(N):
        if play_flag[j] == True:
            k = 1
            break
    if k == 0:
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s1.connect(('localhost', 10050))
        msg = "PLAYSONG|" + imagenames[i].split(".")[0] + ".wav"
        length = len(msg)
        print(msg)
        fullmsg = (struct.pack("!i", length)).decode() + msg
        s1.sendall(fullmsg.encode())
        audio_stream(s1,i)
    else:
        print("Another song is already playing.")
        
    

def audio_stream(s,i):
    p = pyaudio.PyAudio()
    CHUNK = 1024
    global stream
    global play_flag
    global pause_flag
    play_flag[i] = True
    stream = p.open(format=p.get_format_from_width(2),
    channels=2,
    rate=44100,
    output=True,
    frames_per_buffer=CHUNK)
    data = b""
    payload_size = struct.calcsize("Q")
    total_frames = struct.unpack("Q", s.recv(struct.calcsize("Q")))[0] / 1024
    total_frames = int(total_frames) + 1
    print(total_frames)
    frames_written = 0
    while True:
        if play_flag[i] and frames_written < total_frames:
            if pause_flag[i] == False:
                try:
                    while len(data) < payload_size:
                        packet = s.recv(4*1024) # 4K
                        if not packet:
                            break
                        data+=packet
    
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("Q",packed_msg_size)[0]
                    while len(data) < msg_size:
                        data += s.recv(4*1024)
                    frame_data = data[:msg_size]
                    data  = data[msg_size:]
                    frame = pickle.loads(frame_data)
                    stream.write(frame)
                    frames_written += 1
                    if frames_written == total_frames:
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                        s.close()
                        play_flag[i] = False
                        break
                except:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    s.close()
                    play_flag[i] = False
                    break
        else:
            stream.stop_stream()
            stream.close()
            p.terminate()
            s.close()
            play_flag[i] = False
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    s.close()
    play_flag[i] = False
    print('Audio closed')

def recv_all(sock, length):
    data = ''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError('socket closed %d bytes into a %d-byte message' % (len(data), length))
        data += more.decode()
    return data.encode()

def simni(s,i,progress,song_name_label):
    length = struct.unpack("!i", s.recv(4))[0]
    name = imagenames[i].split(".")[0] + ".wav"
    rcvsize = 0
    clientsongs = "clientsongs"
    songpath = os.path.join(clientsongs, name)
    print("SIZE OF FILE IS: " + str(length))
    count = 0
    f = open(songpath, 'wb')
    while rcvsize != length:
        count = count+1
        bytesrcved = s.recv(1024)
        rcvsize = rcvsize + len(bytesrcved)
        f.write(bytesrcved)
        if count%10000 == 0:
            progress["value"] = (rcvsize / length) * 100
            count = 0
    progress.destroy()
    song_name_label.destroy()
    print("Downloaded!.")
    s.close()
        

directory = 'clientimages'

for filename in os.listdir(directory):
    if filename.endswith('.png'):
        file_path = os.path.join(directory, filename)
        try:
            os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

        

#Check if we can connect to server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect(('localhost', 10050))
msg = "HELLO"
length = len(msg)
fullmsg = (struct.pack("!i", length)).decode() + msg
s.sendall(fullmsg.encode())

length = struct.unpack("!i", s.recv(4))[0]
reply = s.recv(length)
reply = reply.decode()
if(reply == ""):
    sys.exit(1)
print(reply)

length = struct.unpack("!i", s.recv(4))[0]
data = s.recv(length)
data = (data.decode()).split('|')
for ime in data:
    imagenames.append(ime)
print(imagenames)
check = 0
clientpath = "clientimages"
while(check < len(imagenames)):
    length = struct.unpack("!i", s.recv(4))[0]
    rcvsize = 0
    imagepath = os.path.join(clientpath, imagenames[check])
    f = open(imagepath, 'wb')

    bytesrcved = s.recv(length)
    rcvsize = rcvsize + len(bytesrcved)
    print(rcvsize)
    f.write(bytesrcved)
    
    print("RECEIVED")
    f.close()
    check = check + 1
  
    


N = len(imagenames)
for i in range(N):
    play_flag.append(False)
    pause_flag.append(False)
sliki = []
for i in range(N):
    slikaname = "clientimages/" + imagenames[i] 
    sliki.append(tk.PhotoImage(file=slikaname, height = 168, width = 300))

    
root.rowconfigure(0, weight = 1)
root.columnconfigure(0, weight = 1)


# Create the canvas and configure it to fill the entire window
canvas = tk.Canvas(root)
canvas.grid(row=0, column=0, sticky='nsew')

# Create the scrollbar and configure it to work with the canvas
scroll = tk.Scrollbar(root, orient = tk.VERTICAL, command = canvas.yview)
scroll.grid(row=0, column=1, sticky='ns', rowspan=100)

canvas.config(yscrollcommand = scroll.set)

# Create the frame to hold the images and buttons
frame = tk.Frame(canvas, width=700, height=N * 170)

# Add the images to the frame
for i in range(N):
    image = sliki[i]
    img_label = tk.Label(frame, image=image)
    img_label.configure(width=300, height=168)
    img_label.grid(row=i, column=0)
    play_button = tk.Button(frame, text='Play', command=lambda x=i: _thread.start_new_thread(song_request,(x,)))
    play_button.grid(row=i, column=1)
    stop_button = tk.Button(frame, text='Stop', command=lambda x=i: falseflag(x))
    stop_button.grid(row=i, column=2)
    pause_button = tk.Button(frame, text='Pause/Unpause', command=lambda x=i: pause_unpause(x))
    pause_button.grid(row=i, column=3)
    download_button = tk.Button(frame, text='Download', command=lambda x=i: _thread.start_new_thread(download_song,(x,)))
    download_button.grid(row=i, column=4)

# Insert the frame into the canvas
item = canvas.create_window((0, 0), window = frame, anchor = tk.NW)

# Update the scrollregion of the canvas to fit the frame
canvas.config(scrollregion = canvas.bbox("all"))

root.mainloop()
sys.exit()