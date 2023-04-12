import pygame
import random
import time
import speech_recognition as sr
import random

from multiprocessing import Process, Queue

import os
import openai

import sys
if sys.version_info[0] == 2:  # the tkinter library changed it's name from Python 2 to 3.
    import Tkinter
    tkinter = Tkinter #I decided to use a library reference to avoid potential naming conflicts with people's programs.
else:
    import tkinter
from PIL import Image, ImageTk
def close_image(event):
    print('exiting')
    event.widget.withdraw()
    event.widget.quit()
    sys.exit()
root = tkinter.Tk()
def showPIL(pilImage):
    
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.overrideredirect(1)
    root.geometry("%dx%d+0+0" % (w, h))
    root.focus_set()    
    # root.bind("<Escape>", close_image)
    root.protocol("WM_DELETE_WINDOW", close_image)
    canvas = tkinter.Canvas(root,width=w,height=h)
    canvas.pack()
    canvas.configure(background='black')
    imgWidth, imgHeight = pilImage.size
    if imgWidth > w or imgHeight > h:
        ratio = min(w/imgWidth, h/imgHeight)
        imgWidth = int(imgWidth*ratio)
        imgHeight = int(imgHeight*ratio)
        pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
    image = ImageTk.PhotoImage(pilImage)
    imagesprite = canvas.create_image(w/2,h/2,image=image)
    root.mainloop()

from typing import List
import tempfile
import subprocess as sub
from subprocess import CalledProcessError
from pdf2image import convert_from_bytes, convert_from_path

def latex_to_images_tempfile(latex_strs: List[str], dpi: int = 150) -> List[Image.Image]:
    images = []
    print('printing out latex to image')
    for latex_str in latex_strs:
        # Create a temporary directory
        try: 
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save the LaTeX string to a temporary .tex file
                tex_path = os.path.join(tmpdir, "temp.tex")
                with open(tex_path, "w") as tex_file:
                    tex_file.write(latex_str)

                # Run pdflatex on the .tex file to generate the PDF
                pdf_path = os.path.join(tmpdir, "temp.pdf")
                sub.run(["pdflatex", "-output-directory", tmpdir, tex_path], 
                        check=True,
                        stdout=sub.DEVNULL,
                        stderr=sub.DEVNULL,
                        )

                # Convert the PDF to an image using pdf2image
                img = convert_from_path(pdf_path, dpi=dpi, fmt="png")[0]

                images.append(img)
            print(f'latex code that compiled: >{latex_str}<')
        except CalledProcessError as e: # if the latex code does not compile, return big loss
            print(f'CalledProcessError, latex code that caused the CalledProcessError: >{latex_str}< does not compile')
            images.append(None)

    return images

# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = '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'

response = openai.Completion.create(
  model="text-davinci-003",
  prompt="Give me the latex code for ",
  temperature=0,
  max_tokens=100,
  top_p=1,
  frequency_penalty=0.2,
  presence_penalty=0
)

# If running on macOS, you may need to set the
# following environment variable before execution
# OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Worker process: get user input
#-----------------------------------
og_prompt = "Give me the latex code for "

command_queue = Queue()

# pilImage = Image.open("pic.png")
# showPIL(pilImage)
def listen():
    r = sr.Recognizer()
    #sr.Microphone.list_microphone_names()
    with sr.Microphone() as source:
        print('Calibrating...')
        r.adjust_for_ambient_noise(source)
        r.energy_threshold = 150
        print('Okay, go!')
        while(1):
            text = ''
            print('about to record')
            audio = r.listen(source)
            # audio = r.record(source,duration = 6)
            print('Recognizing...')
            try:
                text = r.recognize_google(audio)
            except:
                unrecognized_speech_text = 'Sorry, I didn\'t catch that.'
                text = unrecognized_speech_text
            print(text)
            if 'latex' in text:
                prompt = og_prompt +'\n' + text + '\n'
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=prompt,
                    temperature=0,
                    max_tokens=100,
                    top_p=1,
                    frequency_penalty=0.2,
                    presence_penalty=0
                    )
                response_text = response['choices'][0]['text']
                print(response_text)
                length = len(og_prompt +'\n' + text + '\n')
                print(f'length: {length}')
                just_end = response_text
                print(f'just end: {str(just_end)}')

                try:
                    command_queue.put(just_end.strip())
                except:
                    print(f'wrong format: {just_end.strip()}')
                    pass


# Main execution loop
#-----------------------------------


listener = Process(target=listen)
listener.start()

done = False
while not done:
        try:
            command = command_queue.get(block=False, timeout=0.1)
            print('got command')
            print(command)
            
            real_latex = """\documentclass{article}\\begin{document}""" + command + """\end{document}"""
            latex_image = latex_to_images_tempfile([real_latex])[0]

            print('printing image')
            # pilImage = Image.open("pic.png")
            showPIL(pilImage=latex_image)
            print('image printed')
        except:
            pass


        time.sleep(10)          # pauses execution until 1/60 seconds
                                # have passed since the last tick
listener.kill()