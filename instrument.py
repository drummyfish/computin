# Computing musical instrument for python 2. Requires pyaudio.
#
# Miloslav "tastyfish" Ciz, 2015

import math
import pyaudio
import time
from Tkinter import *
import random
import wave
import struct
import sys

#-------------------------------

tones = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

def frequency_to_tone(frequency):
  n = int(round(12 * math.log(frequency / 440.0, 2) + 49) - 1)

  octave = n / 12
  tone = n % 12

  return tones[(tone) % len(tones)] + str(octave)

def note_to_gray_value(note):
  if note[1:2] == "#":
    return 0
  elif note[:1] == "E" or note[:1] == "B":
    return 200

  return 255

class tonePLayer:
  def __init__(self, sound_name):
    self.frequency = 400
    self.volume = 0.5
    self.playing = False
    self.bitrate = 16000   # frames per second
    self.phase = 0
    self.phase2 = 0      # 2nd harmonics
    self.phase3 = 0      # 3rd harmonics
    self.phase4 = 0      # 4th harmonics

    self.pi_2 = 2 * math.pi
    self.quotient = self.frequency / float(self.bitrate)

    self.harmonics_ratio = (25, 25, 25, 25)

    def callback(in_data, frame_count, time_info, status_flag):
      result = ""

      if not self.playing:
        for i in range(frame_count):
          result += chr(128)
      else:
        if self.use_loaded_sound:      # sound loaded from file
          for i in range(frame_count):
            result += chr(128 + int(self.volume * self.sound_data[int(self.sound_position)] / 32768.0 * 120))
            speed = self.frequency / 440.0
            self.sound_position = (self.sound_position + speed) % (len(self.sound_data) - 1)
        else:                          # synthesized sound
          for i in range(frame_count):
            self.phase += self.quotient
            self.phase2 += 2 * self.quotient
            self.phase3 += 3 * self.quotient
            self.phase4 += 4 * self.quotient

            result += chr(int( self.volume * (
              math.cos(self.phase) * self.harmonics_ratio[0] +
              math.cos(self.phase2) * self.harmonics_ratio[1] +
              math.cos(self.phase3) * self.harmonics_ratio[2] +
              math.cos(self.phase4) * self.harmonics_ratio[3]
              ) + 128))

      return (result, 0)

    self.audio = pyaudio.PyAudio()
    self.audio_stram = self.audio.open(format=self.audio.get_format_from_width(
        1), channels=1, frames_per_buffer=128, rate=self.bitrate, output=True, stream_callback=callback)
    
    # load the wav sound, otherwise use the synthesised one
    
    try:
      wave_file = wave.open(sound_name,"r")     # sound that should be 440 hz
    
      length = wave_file.getnframes()
      self.sound_data = []
      self.sound_position = 0
      
      for i in range(0,length):
        wave_data = wave_file.readframes(1)
        data = struct.unpack("<h", wave_data)
        self.sound_data.append(data[0])
      
      self.use_loaded_sound = True
    except Exception as e:
      self.use_loaded_sound = False
      print("ERROR: could not load the sound file. " + str(e))

  def set_volume(self, volume):
    self.volume = volume

  def is_playing(self):
    return self.playing

  def set_pitch(self, frequency):
    self.frequency = frequency
    self.quotient = self.pi_2 * self.frequency / float(self.bitrate)

  def play(self):
    self.playing = True

  def stop(self):
    self.playing = False

class configDialog:
  def __init__(self, master):
    self.master = master
    self.window = Toplevel(master)
    
    self.lowest_frequency_var = StringVar()
    self.highest_frequency_var = StringVar()
    self.window_width_var = StringVar()
    self.window_height_var = StringVar() 
    self.sound_file_var = StringVar()
    self.linear_var = IntVar()
    
    Label(self.window, text="lowest frequency").grid(row=1, column=1, sticky=W)
    Entry(self.window, textvariable=self.lowest_frequency_var).grid(row=1, column=2, sticky=W)
    
    Label(self.window, text="highest frequency").grid(row=2, column=1, sticky=W)
    Entry(self.window, textvariable=self.highest_frequency_var).grid(row=2, column=2, sticky=W)
    
    Label(self.window, text="sound file").grid(row=3, column=1, sticky=W)
    Entry(self.window, textvariable=self.sound_file_var).grid(row=3, column=2, sticky=W)

    Label(self.window, text="(specify 440 Hz (tone A) wav mono sound (16 kHz sampling) or leave empty)").grid(row=4, column=1, sticky=W, columnspan=2)
    
    Label(self.window, text="linear scale").grid(row=5, column=1, sticky=W)
    Checkbutton(self.window, text="", variable=self.linear_var).grid(row=5, column=2, sticky=W)
    
    Label(self.window, text="window width").grid(row=6, column=1, sticky=W)
    Entry(self.window, textvariable=self.window_width_var).grid(row=6, column=2, sticky=W)

    Label(self.window, text="window height").grid(row=7, column=1, sticky=W)
    Entry(self.window, textvariable=self.window_height_var).grid(row=7, column=2, sticky=W)

    self.window_width_var.set("800")
    self.window_height_var.set("600") 
    self.lowest_frequency_var.set("500")
    self.highest_frequency_var.set("3000")
    self.sound_file_var.set("")
    self.linear_var.set(0)
    
    button = Button(self.window, text="OK", command=self.ok)
    button.grid(row=8, column=1, sticky=W, columnspan=2)
    button.focus_set()
    
    master.withdraw()
    
  def ok(self):
    self.window.destroy()
    self.master.deiconify()

class Gui:
  def __init__(self, master, window_width, window_height, sound_name, pitch_from, pitch_to, linear):          # if no sound is given, synthesized voice is used
    self.player = tonePLayer(sound_name)

    self.window_width = window_width
    self.window_height = window_height
    self.pitch_range = [100, 3500]
    
    if pitch_from != None:
      self.pitch_range[0] = int(pitch_from)
    
    if pitch_to != None:
      self.pitch_range[1] = int(pitch_to)
    
    self.pitch_difference = self.pitch_range[1] - self.pitch_range[0]
    self.current_pitch = 0
    self.current_volume = 0
    self.info_text = None

    self.linear = linear
    self.linear_helper_value_1 = math.log(self.pitch_range[1], 2)
    self.linear_helper_value_2 = math.log(self.pitch_range[0], 2)

    frame = Frame(master)
    master.wm_title("computin")
    master.resizable(width=FALSE, height=FALSE)
    frame.pack()

    def x_position_to_pitch(x):
      if self.linear:
        ratio = x / float(self.window_width)
        return pow(2,ratio * self.linear_helper_value_1 + (1.0 - ratio) * self.linear_helper_value_2)
      else:
        return x / float(self.window_width) * (self.pitch_difference) + self.pitch_range[0]

    def mouse_move(event):
      self.current_pitch = x_position_to_pitch(event.x)
      self.current_volume = 1 - event.y / float(self.window_height)

      if self.current_pitch < self.pitch_range[0] or self.current_pitch > self.pitch_range[1] or self.current_volume < 0 or self.current_volume > 1:
        return

      self.player.set_pitch(self.current_pitch)
      self.player.set_volume(self.current_volume)
      self.redraw_text()

    def mouse_release(event):
      self.player.stop()
      self.redraw_text()

    def mouse_press(event):
      self.player.play()
      self.redraw_text()

    self.canvas = Canvas(
        master, width=self.window_width, height=self.window_height)
    self.canvas.bind("<Motion>", mouse_move)

    self.canvas.bind("<Button>", mouse_press)
    self.canvas.bind("<ButtonRelease>", mouse_release)

    self.canvas.pack()

    self.background = PhotoImage(
        width=self.window_width, height=self.window_height)
    self.canvas.create_image(
        (self.window_width / 2, self.window_height / 2), image=self.background, state="normal")

    self.canvas.create_rectangle((40, 25, 170, 70), fill="#FFFFFF")

    def pixel(image, pos, color):
      r, g, b = color
      x, y = pos
      image.put("#%02x%02x%02x" % (r, g, b), (y, x))

    for x in range(self.window_width):

      value = note_to_gray_value(frequency_to_tone(x_position_to_pitch(x)))
      color = (value, value, value)

      for y in range(self.window_height):
        pixel(self.background, (y, x), color)

  def redraw_text(self):
    if self.info_text:
      self.canvas.delete(self.info_text)

    self.info_text = self.canvas.create_text((50, 50), text=str(
        self.current_pitch) + " Hz \n" + frequency_to_tone(self.current_pitch), fill="red", anchor=W)

root = Tk()
dialog = configDialog(root)
root.wait_window(dialog.window)
app = Gui(root,
          int(dialog.window_width_var.get()),
          int(dialog.window_height_var.get()),
          dialog.sound_file_var.get(),
          int(dialog.lowest_frequency_var.get()),
          int(dialog.highest_frequency_var.get()),
          bool(dialog.linear_var.get()))
root.mainloop()
