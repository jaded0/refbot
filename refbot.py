import pygame
import random
import time
import speech_recognition as sr
import random

from multiprocessing import Process, Queue

import os
import openai

import io

import configparser
import glob

import sys
if sys.version_info[0] == 2:  # the tkinter library changed it's name from Python 2 to 3.
    import Tkinter
    tkinter = Tkinter #I decided to use a library reference to avoid potential naming conflicts with people's programs.
else:
    import tkinter
from PIL import Image, ImageTk, ImageDraw, ImageOps
# def close_image(event):
#     print('exiting')
#     event.widget.withdraw()
#     event.widget.quit()
#     sys.exit()
# root = tkinter.Tk()
# def showPIL(pilImage):
    
#     w, h = root.winfo_screenwidth(), root.winfo_screenheight()
#     root.overrideredirect(1)
#     root.geometry("%dx%d+0+0" % (w, h))
#     root.focus_set()    
#     # root.bind("<Escape>", close_image)
#     root.protocol("WM_DELETE_WINDOW", close_image)
#     canvas = tkinter.Canvas(root,width=w,height=h)
#     canvas.pack()
#     canvas.configure(background='black')
#     imgWidth, imgHeight = pilImage.size
#     if imgWidth > w or imgHeight > h:
#         ratio = min(w/imgWidth, h/imgHeight)
#         imgWidth = int(imgWidth*ratio)
#         imgHeight = int(imgHeight*ratio)
#         pilImage = pilImage.resize((imgWidth,imgHeight), Image.ANTIALIAS)
#     image = ImageTk.PhotoImage(pilImage)
#     imagesprite = canvas.create_image(w/2,h/2,image=image)
#     root.mainloop()

def trim_image(image, ):
    # Get bounding box of text and trim to it
    bbox = ImageOps.invert(image).getbbox()
    trimmed = image.crop(bbox)

    # Add new white border, then new black, then new white border
    res = ImageOps.expand(trimmed, border=10, fill=(255,255,255))
    res = ImageOps.expand(res, border=5, fill=(0,0,0))
    res = ImageOps.expand(res, border=5, fill=(255,255,255))
    # res.save('result.png')
    return res

def display_latex_image(pil_image, screen):
    # pil_image = your_latex_to_image_function(latex_code)  # Replace this with your function

    # Convert the PIL image to a Pygame surface
    imgdata = io.BytesIO()
    pil_image.save(imgdata, format='PNG')
    imgdata.seek(0)
    pygame_image = pygame.image.load(imgdata).convert()

    # Display the Pygame surface on the screen
    screen.blit(pygame_image, (0,0))  # Replace 'x' and 'y' with the desired position
    pygame.display.flip()  # Update the screen

def resize_image(image, max_width, max_height):
    width, height = image.size
    aspect_ratio = float(width) / float(height)

    if width > max_width:
        width = max_width
        height = int(width / aspect_ratio)
    if height > max_height:
        height = max_height
        width = int(height * aspect_ratio)

    return image.resize((width, height), Image.LANCZOS)

def display_latex_image_cached(pil_image, screen):
    # Clear the screen
    screen.fill((0, 0, 0))  # Fill the screen with black (or any other desired color)

    # Read the cached images from the 'images' folder
    cached_images = []
    for img_path in glob.glob('images/*.png'):
        img = Image.open(img_path)
        img = resize_image(img, 400, 300)  # Resize the older images
        cached_images.append(img)

    # Resize the current image and cache it
    pil_image = resize_image(pil_image, 1300, 600)  # Adjust the size as needed
    timestamp = str(int(time.time()))
    pil_image.save(f'images/current_image_{timestamp}.png')
    cached_images.insert(0, pil_image)  # Add the current image to the front of the list

    # Calculate the positions of the images
    x, y = 0, 0
    max_height = 0
    positions = []
    for img in cached_images:
        width, height = img.size
        if x + width > screen.get_width():
            x = 0
            y += max_height
            max_height = 0
        positions.append((x, y))
        x += width
        max_height = max(max_height, height)

    # Display the images on the screen
    for img, pos in zip(cached_images, positions):
        imgdata = io.BytesIO()
        img.save(imgdata, format='PNG')
        imgdata.seek(0)
        pygame_image = pygame.image.load(imgdata).convert()
        screen.blit(pygame_image, pos)

    pygame.display.flip()  # Update the screen





from typing import List
import tempfile
import subprocess as sub
from subprocess import CalledProcessError
from pdf2image import convert_from_bytes, convert_from_path

def latex_to_images_tempfile(latex_strs: List[str], dpi: int = 150) -> List[Image.Image]:
    images = []
    print('converting latex to image')
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
                # print(f'pdf path: {pdf_path}')
                sub.run(["pdflatex", "-output-directory", tmpdir, tex_path], 
                        check=True,
                        stdout=sub.DEVNULL,
                        stderr=sub.DEVNULL,
                        timeout=10,
                        )
                # print('converting to an image')
                # Convert the PDF to an image using pdf2image
                img = convert_from_path(pdf_path, dpi=dpi, fmt="png")[0]

                images.append(img)
            # print(f'latex code that compiled: >{latex_str}<')
        except CalledProcessError as e: # if the latex code does not compile, return big loss
            print(f'CalledProcessError, latex code that caused the CalledProcessError: >{latex_str}< does not compile')
            images.append(None)

    return images

# openai.api_key = os.getenv("OPENAI_API_KEY")
cfg = configparser.ConfigParser()
cfg.read('config.cfg')

print(cfg.get('KEYS', 'openai', raw=''))
openai.api_key = cfg.get('KEYS', 'openai', raw='') 
# [KEYS]
# openai: 

# response = openai.Completion.create(
#   model="text-davinci-003",
#   prompt="Give me the latex code for ",
#   temperature=0,
#   max_tokens=100,
#   top_p=1,
#   frequency_penalty=0.2,
#   presence_penalty=0
# )

def wakeword(text):
    WAKE_WORDS = ['latex', 'attack', 'la tech', "let's check", "the text", 'the tech', 'the techs','a text', 'a tech', 'a techs', 'latex', 'latexs', 'latexes', 'latexi', 'latexes', 'latexis', 'lat', 'tech', 'the type', 'tag', 'talk', 'protect', 'task', 'letek', 'detect', 'lapeque', 'text', 'check', 'litek']
    text = text.lower()
    for phrase in WAKE_WORDS:
        if phrase in text:
            return True
    return False

# If running on macOS, you may need to set the
# following environment variable before execution
# OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Worker process: get user input
#-----------------------------------
# og_prompt = "Extract the segment of the following transcribed recording that is relevant to the request for latex reference information, then return the latex code for the relevant request:"
with open('og_prompt.txt', 'r') as file:
    og_prompt = file.read()

with open('tex_header.txt', 'r') as file:
    header = file.read()
print(f'og prompt {og_prompt}\n header {header}')

# pilImage = Image.open("pic.png")
# showPIL(pilImage)
def listen(command_queue):
    r = sr.Recognizer()
    #sr.Microphone.list_microphone_names()
    with sr.Microphone() as source:
        print('Calibrating...')
        r.adjust_for_ambient_noise(source, duration=5)
        r.energy_threshold = 200
        r.pause_threshold=0.5    
        
        print('Okay, go!')
        while(1):
            text = ''
            print('listening now...')
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=15)
                # audio = r.record(source,duration = 5)
                print('Recognizing...')
                start = time.time()
                # alts = [x['transcript'] for x in r.recognize_google(audio, language='en-US', show_all=True)['alternative']]
                text = r.recognize_whisper(audio, model='medium.en', show_dict=True, )['text']
                # print(alts)
                # text = alts[0]
                # if 'latex' not in text:
                #     for choice in alts:
                #         if 'latex' in choice:
                #             text = choice
                #             break
            except Exception as e:
                start = time.time()
                unrecognized_speech_text = f'Sorry, I didn\'t catch that. Exception was: {e}s'
                text = unrecognized_speech_text
            print(text)
            if wakeword(text):
                prompt = og_prompt +'\n' + text + '\n\n' + """Latex code:\n""" + header
                response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=prompt,
                    temperature=0,
                    max_tokens=1000,
                    top_p=1,
                    frequency_penalty=0.2,
                    presence_penalty=0
                    )
                response_text = response['choices'][0]['text']
                # check if there's a better version.
                # if 'latex' not in response_text:
                #     for choice in response['choices']:
                #         if 'latex' in choice['text']:
                #             response_text = choice['text']
                #             break
                # print(response_text)
                length = len(og_prompt +'\n' + text + '\n')
                # print(f'length: {length}')
                just_end = str(response_text.strip())
                # print(f'just end: {just_end}')

                try:
                    # print(f'putting in the command{just_end}')
                    command_queue.put(just_end, block=False)
                    # command_queue.put(just_end, block=True, timeout=1)
                    # print(f'command put in. the queue length is {command_queue.qsize()}')
                except:
                    print(f'wrong format: {just_end.strip()}')
                    pass
                
            print(f'time to recognize: {time.time() - start}')


# Main execution loop
#-----------------------------------
if __name__ == '__main__':
    # test = """\documentclass{article}\\begin{document}$\Omega$\end{document}"""
    # # test = 'wat'
    # print(test)
    # with tempfile.TemporaryDirectory() as tmpdir:
    #     # Save the LaTeX string to a temporary .tex file
    #     tex_path = os.path.join(tmpdir, "temp.tex")
    #     with open(tex_path, "w") as tex_file:
    #         tex_file.write(test)
    #     pdf_path = os.path.join(tmpdir, "temp.pdf")
    #     print(f'pdf path: {pdf_path}')
    #     sub.run(["pdflatex", "-output-directory", tmpdir, tex_path], 
    #             check=True,
    #             stdout=sub.DEVNULL,
    #             stderr=sub.DEVNULL,
    #             timeout=45,
    #             )
    #     print('converting to an image')
    #     # Convert the PDF to an image using pdf2image
    #     img = convert_from_path(pdf_path, dpi=150, fmt="png")[0]
    #     img.save('test.png')
        
    pygame.init()
    # screen = pygame.display.set_mode((1000,1000))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    screen_width, screen_height = screen.get_size()
    indicator_x, indicator_y = screen_width - 100, 50


    command_queue = Queue()
    listener = Process(target=listen, args=(command_queue,))
    listener.start()

    done = False
    while not done:
        # time.sleep(1)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True

        command = 'none'
        try:
            # print(f'command queue size: {command_queue.qsize()}')
            command = command_queue.get(block=False)
            # command = command_queue.get(block=True, timeout=1)
            # command = '$\Omega$' + """\end{document}"""
            # print('got command for sure')
        except Exception as e:
            pass



        if command == 'none':
            continue

        # print('got command?')
        # print(command)

        # show green indicator on the top right of the screen
        pygame.draw.circle(screen, (0, 255, 0), (indicator_x, indicator_y), 50)
        pygame.display.flip()
        try:
            start_time = time.time()
            real_latex = header + command #+ """\end{document}"""
            # print(f'latex: {real_latex}')
            latex_image = latex_to_images_tempfile([real_latex], dpi=300)[0]

            # print('printing and saving image')
            latex_image.save('ex_pic.png')
            # pilImage = Image.open("pic.png")
            # showPIL(pilImage=latex_image)
            latex_image = trim_image(latex_image)
            latex_image.save('trimmed.png')
            # display_latex_image(latex_image, screen)
            display_latex_image_cached(latex_image, screen)
            print(f'time to print: {time.time() - start_time}')
            # remove green indicator
            pygame.draw.circle(screen, (0, 0, 0), (indicator_x, indicator_y), 50)
            pygame.display.flip()
        except Exception as e:
            print(f'error printing image: {e}')
            # place red indicator on the top right of the screen
            pygame.draw.circle(screen, (255, 0, 0), (indicator_x, indicator_y), 50)
            pygame.display.flip()
            pass
        
        
        time.sleep(1)          # pauses execution until 1/60 seconds
                                # have passed since the last tick
    listener.terminate()