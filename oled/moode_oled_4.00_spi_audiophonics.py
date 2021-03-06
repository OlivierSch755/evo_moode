﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUDIOPHONICS RASPDAC MINI OLED Script #
# 11/09/2018 
# MAJ 24/11/2020 : portage python3
import sys


import os
import time
import socket
import re
import subprocess
from subprocess import Popen, PIPE

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1322
import RPi.GPIO as GPIO
serial = spi(port=0, device=0, gpio_DC=27, gpio_RST=24)
device = ssd1322(serial, rotate=0, mode="1")

mpd_music_dir        = "/var/lib/mpd/music/"
title_height        = 40
scroll_unit        = 2
oled_width        = 256
oled_height        = 64

def make_font(name, size):
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)

font_title              = make_font('msyh.ttf', 26)
font_info        = make_font('msyh.ttf', 20)
font_vol        = make_font('msyh.ttf', 55)
font_ip            = make_font('msyh.ttf', 15)
font_time        = make_font('msyh.ttf', 18)
font_20            = make_font('msyh.ttf', 18)
font_date        = make_font('arial.ttf', 25)
font_logo        = make_font('arial.ttf', 42)
font_32            = make_font('arial.ttf', 50)
awesomefont        = make_font("fontawesome-webfont.ttf", 16)
awesomefontbig    = make_font("fontawesome-webfont.ttf", 42)

speaker            = "\uf028"
wifi            = "\uf1eb"
link            = "\uf0e8"
clock            = "\uf017"

mpd_host        = 'localhost'
mpd_port        = 6600
mpd_bufsize        = 8192


def getWanIP():
    #can be any routable address,
    fakeDest = ("223.5.5.5", 53)
    wanIP = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(fakeDest)
        wanIP = s.getsockname()[0]
        s.close()
    except:
        pass
    return wanIP

def GetLANIP():
   cmd = "ip addr show eth0 | grep inet  | grep -v inet6 | awk '{print $2}' | cut -d '/' -f 1"
   p = Popen(cmd, shell=True, stdout=PIPE)
   output = p.communicate()[0]
   return output[:-1]
   
# OLED images
image        = Image.new('1', (oled_width, oled_height))
draw        = ImageDraw.Draw(image)
music_file    =""
shift        = 0
title_image     = Image.new('L', (oled_width, title_height))
title_offset    = 0
current_page = 0
vol_val_store = 0
screen_sleep = 0
timer_vol = 0
input_counter = 0
screensave = 3

# Socket 
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.connect((mpd_host, mpd_port))
soc.recv(mpd_bufsize)

soc.sendall(b'commands\n')
rcv = soc.recv(mpd_bufsize)
shift        = 1
music_file    = ""

with canvas(device) as draw:
    draw.text((3, 10),"Audiophonics", font=font_logo,fill="white")
time.sleep(2)

try:
    while True:
        soc.send(b'currentsong\n')
        buff  = soc.recv(mpd_bufsize)
        song_list = buff.decode('utf-8').splitlines()
        soc.send(b'status\n')
        buff        = soc.recv(mpd_bufsize)
        state_list  = buff.decode('utf-8').splitlines()
        info_state      = ""
        info_audio      = ""
        info_elapsed    = 0
        info_duration   = 0
        info_title      = ""
        info_artist     = ""
        info_album      = ""
        info_name = ""
        info_file    = ""
        bit_val        = ""
        samp_val    = ""
        time_val    = time_min = time_sec = vol_val = audio_val = 0
        

        for line in range(0,len(state_list)):
            if state_list[line].startswith("state: "):
                info_state = state_list[line].replace("state: ", "")
            if state_list[line].startswith("elapsed: "):   #info_elapsed    = float(state_list[line].replace("elapsed: ", ""))

                time_val = float(state_list[line].replace("elapsed: ", ""))
                time_bar = time_val
                time_min = time_val/60
                time_sec = time_val%60
                time_min = "%2d" %time_min
                time_sec = "%02d" %time_sec
                time_val = str(time_min)+":"+str(time_sec)
            if state_list[line].startswith("time: "):      info_duration   = float(state_list[line].split(":")[2])

            # Volume
            if state_list[line].startswith("volume: "):     vol_val      = state_list[line].replace("volume: ", "")
            # Volume NULL
            if vol_val == "" : 
                vol_val = "0"
                subprocess.Popen(['mpc', 'volume', '0' ])
            # Sampling rate / bit 
            if state_list[line].startswith(r"audio: "):
                audio_val = state_list[line]
                audio_val = audio_val.replace("audio: ", "")
                audio_val = re.split(':',audio_val)

                bit_val = audio_val[1]+'bit '
                if audio_val[0] == '22050':
                    samp_val = '22.05k/'
                elif audio_val[0] == '32000':
                    samp_val = '32k/'
                elif audio_val[0] == '44100':
                    samp_val = '44.1k/'
                elif audio_val[0] == '48000':
                    samp_val = '48k/'
                elif audio_val[0] == '88200':
                    samp_val = '88.2k/'
                elif audio_val[0] == '96000':
                    samp_val = '96k/'
                elif audio_val[0] == '176400':
                    samp_val = '176.4k/'
                elif audio_val[0] == 'dsd64':
                    samp_val = 'DSD64/'
                    bit_val = '1bit'
                elif audio_val[0] == '192000':
                    samp_val = '192k/'
                elif audio_val[0] == '352800':
                    samp_val = '352.8k/'
                elif audio_val[0] == 'dsd128':
                    samp_val = 'DSD128/'
                    bit_val = '1bit'
                elif audio_val[0] == '384000':
                    samp_val = '384k/'
                elif audio_val[0] == '705600':
                    samp_val = '705.6k/'
                elif audio_val[0] == 'dsd256':
                    samp_val = 'DSD256/'
                    bit_val = '1bit'
                elif audio_val[0] == '768000':
                    samp_val = '768k/'
                elif audio_val[0] == '1411200':
                    samp_val = 'DSD512/'
                    bit_val = '1bit'
                elif audio_val[0] == '6144000':
                    samp_val = 'DSD1024/'
                    bit_val = '1bit'
                else:
                    samp_val = state_list[line].replace("audio: ", "")
                    bit_val = ""

                if audio_val[1] == 'f':
                    bit_val = '24bit'

        for song_line in range(0,len(song_list)):
            if song_list[song_line].startswith("file: "):       info_file       = song_list[song_line].replace("file: ", "")
            if song_list[song_line].startswith("Artist: "):     info_artist     = song_list[song_line].replace("Artist: ", "")
            if song_list[song_line].startswith("Album: "):      info_album      = song_list[song_line].replace("Album: ", "")
            if song_list[song_line].startswith("Title: "):      info_title      = song_list[song_line].replace("Title: ", "")
            if song_list[song_line].startswith("Name: "):      info_name      = song_list[song_line].replace("Name: ", "") 
        
       
        # Volume change screen
        if vol_val != vol_val_store : timer_vol = 20
        if timer_vol > 0 :
            with canvas(device) as draw:
                vol_width, char = font_vol.getsize(vol_val)
                x_vol = ((oled_width - vol_width) / 2)
                # Volume Display
                draw.text((5, 5), text="\uf028", font=awesomefontbig, fill="white")
                draw.text((x_vol, -15), vol_val, font=font_vol, fill="white")
                # Volume Bar
                draw.rectangle((0,53,255,60), outline=1, fill=0)
                Volume_bar = ((int(float(vol_val)) * 2.52)+2)
                draw.rectangle((2,55,Volume_bar,58), outline=0, fill=1)
            vol_val_store = vol_val
            timer_vol = timer_vol - 1
            screen_sleep = 0
            time.sleep(0.1)
  

        # Play screen
        elif info_state != "stop":

            if info_title == "" :
                name    = info_file.split('/')
                name.reverse()
                info_title  = name[0]

                try:
                    info_album  = name[1]
                except:
                    info_album  = ""

                try:
                    info_artist = name[2]
                except:
                    info_artist = ""

            if info_name != "" : info_artist = info_name

            if info_duration != 0 :
                time_bar = time_bar / info_duration * 256
            

            if info_file != music_file or time_bar < 5 :
                #Called one time / file
                music_file  = info_file;
                # Generate title image
    
                #if title_width < artist_width:
                #    title_width = artist_width
                if info_duration != 0 :
                    dura_min = info_duration/60
                    dura_sec = info_duration%60
                    dura_min = "%2d" %dura_min
                    dura_sec = "%02d" %dura_sec
                    dura_val = "/ " + str(dura_min)+":"+str(dura_sec)
                else : 
                    dura_val = ""
                artist_offset    = 10;
                album_offset    = 10;
                title_offset     = 10;
                title_width, char  = font_info.getsize(info_title)
                artist_width, char  = font_info.getsize(info_artist)
                album_width, char  = font_info.getsize(info_album)
                bitrate_width, char = font_time.getsize(samp_val + bit_val)
                
                current_page = 0

            # OFFSETS*****************************************************
            x_artist   = 0
            if oled_width < artist_width :
                if artist_width < -(artist_offset + 20) :
                    artist_offset    = 0

                if artist_offset < 0 :
                    x_artist   = artist_offset

                artist_offset    = artist_offset - scroll_unit
                
            x_album   = 0
            if oled_width < album_width :
                if album_width < -(album_offset + 20) :
                    album_offset    = 0

                if album_offset < 0 :
                    x_album   = album_offset

                album_offset    = album_offset - scroll_unit    
            
            x_title   = 0
            if oled_width < title_width :
                if title_width < -(title_offset + 20) :
                    title_offset    = 0

                if title_offset < 0 :
                    x_title   = title_offset

                title_offset    = title_offset - scroll_unit    
            
            x_bitrate = (oled_width - bitrate_width) / 2



            with canvas(device) as draw:
                if current_page < 150 :    
                    draw.text((x_title, -7), info_title, font=font_info, fill="white")
                    if title_width < -(title_offset - oled_width) and title_width > oled_width :
                        draw.text((x_title + title_width + 10,-7), "- " + info_title, font=font_info, fill="white")                    
                    draw.text((x_bitrate, 20), (samp_val + bit_val), font=font_time, fill="white")                    
                    if info_state == "pause": 
                        draw.text((0, 43), text="\uf04c", font=awesomefont, fill="white")
                    else:
                        draw.text((0, 41), time_val, font=font_time, fill="white")
                        draw.text((55, 41), dura_val, font=font_time, fill="white")
                        #draw.text((58, 48), text="\uf001", font=awesomefont, fill="white")    
                    draw.rectangle((0,40,time_bar,44), outline=0, fill=1)
                    draw.text((200, 44), text="\uf028", font=awesomefont, fill="white")    
                    draw.text((220, 41), vol_val, font=font_time, fill="white")
                
                    current_page = current_page + 1
                    artist_offset = 10
                    album_offset = 10                        
        
                elif current_page < 300    :
                    # artist name
                    draw.text((x_artist,-7), info_artist, font=font_info, fill="white")
                    if artist_width < -(artist_offset - oled_width) and artist_width > oled_width :
                        draw.text((x_artist + artist_width + 10,-7), "- " + info_artist, font=font_info, fill="white")
                    # album name
                    draw.text((x_album, 14), info_album, font=font_info, fill="white")
                    if album_width < -(album_offset - oled_width) and album_width > oled_width :
                        draw.text((x_album + album_width + 10,14), "- " + info_album, font=font_info, fill="white")
                    # Bottom line
                    if info_state == "pause": 
                        draw.text((0, 43), text="\uf04c", font=awesomefont, fill="white")
                    else:
                        draw.text((0, 41), time_val, font=font_time, fill="white")
                        draw.text((55, 41), dura_val, font=font_time, fill="white")
                    draw.rectangle((0,40,time_bar,44), outline=0, fill=1)
                    draw.text((200, 44), text="\uf028", font=awesomefont, fill="white")
                    draw.text((220, 41), vol_val, font=font_time, fill="white")
                    current_page = current_page + 1
                    
                    if current_page == 300 :
                        current_page = 0
                        title_offset = 10
                        
                
            time.sleep(0.05)
        else:
            # Time IP screen
            music_file  = ""
            ip = getWanIP()
            #ip = str(GetLANIP())
            if screen_sleep < 20000 :
                with canvas(device) as draw:
                    #draw.text((1, -6),"Volumio", font=font_logo,fill="white")
                    if ip != "":
                        draw.text((140, 45), ip, font=font_ip, fill="white")
                        draw.text((120, 45), link, font=awesomefont, fill="white")
                    else:
                        draw.text((140, 45),time.strftime("192.168.211.1"), font=font_ip, fill="white")
                        draw.text((120, 45), wifi, font=awesomefont, fill="white")

                    draw.text((28,-10),time.strftime("%X"), font=font_32,fill="white")
                    draw.text((20, 40), vol_val, font=font_time, fill="white")
                    draw.text((1, 43), text="\uf028", font=awesomefont, fill="white")
                screen_sleep = screen_sleep + 1
            else :
                with canvas(device) as draw:
                    screensave += 2
                    if screensave > 120 : 
                        screensave = 3
                    draw.text((screensave, 45), ".", font=font_time, fill="white")
                time.sleep(1)                            
            time.sleep(0.1)
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)



