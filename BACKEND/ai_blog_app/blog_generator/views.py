from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from .models import BlogPost


from django.conf import settings

import os

import assemblyai as aai


from openai import OpenAI


# Create your views here.
@login_required # LOGIN redirect url defined in settings.py
def index(request):
    return render(request,'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except(KeyError, json.JSONDecodeError):
            return JsonResponse({'error':'Invalid data sent'},status=400)
        
        # Get yt title
        title = yt_title(yt_link)
        
        # Get transcript
        #  Using a platform named AssemblyAI
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error':'Transcription failed'},status=500)


        # use OpenAI to generate the blog
        # blog_content = generate_blog_from_transcription(transcription)
        # if not blog_content:
        #     return JsonResponse({'error':'Blog generation failed'},status=500)

        # save blog article to the database
        new_blog_Article = BlogPost.objects.create(
            user = request.user, # THe currently logged in user
            youtube_title = title,
            youtube_link = yt_link,
            generated_content = transcription,
        )
        new_blog_Article.save() # Saves the article into the database

        # return blog article as a  response
        return JsonResponse({'content':transcription})


    else:
        return JsonResponse({'error':'Invalid request method'},  status = 405)
    pass

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    print("title",title)
    return title

import os
from pytube import YouTube
from django.conf import settings  # Assuming Django settings for MEDIA_ROOT

# def download_audio(link):
#     yt = YouTube(link)
#     video = yt.streams.filter(only_audio=True).first()

#     # Check if the file already exists
#     filename = video.title + '.mp3'
#     output_file = os.path.join(settings.MEDIA_ROOT, filename)
#     if os.path.exists(output_file):
#         print(f"File '{filename}' already exists. Skipping download.")
#         return output_file

#     # If file doesn't exist, download it
#     out_file = video.download(output_path=settings.MEDIA_ROOT)
#     base, ext = os.path.splitext(out_file)
#     new_file = base + '.mp3'
#     os.rename(out_file, new_file)
#     return new_file

import yt_dlp

import os
import yt_dlp
from django.conf import settings

def download_audio(link):
    ffmpeg_path = r'C:\Users\DELL\Downloads\Compressed\ffmpeg-2024-07-07-git-0619138639-essentials_build\bin'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'),
        'ffmpeg_location': ffmpeg_path
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(link, download=False)
        filename = info_dict.get('title', 'audio') + '.mp3'
        output_file = os.path.join(settings.MEDIA_ROOT, filename)
        
        if os.path.exists(output_file):
            print(f"File '{filename}' already exists. Skipping download.")
            return output_file
        
        ydl.download([link])
        return output_file


def get_transcription(link):
    audio_file = download_audio(link)

    # AssemnlyAI key
    aai.settings.api_key = "a8e73355a9a24639aa7fa0154ff34053"
    # transcriber object
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    # Use AssemblyAI to get the transcription
    
    # Save the transcription to the database

    # Return the transcription as a response

    return transcript.text


    pass

# def generate_blog_from_transcription(transcription):
#     openai.api_key = "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"
    
#     prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
#     response = openai.Completion.create(
#         model="text-davinci-003",
#         prompt=prompt,
#         max_tokens=1000
#     )



#     generated_content = response.choices[0].text.strip()

#     return generated_content


def generate_blog_from_transcription(transcription):
    api_key = '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'
    
    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    client = OpenAI(
        # This is the default and can be omitted
        # api_key=os.environ.get("OPENAI_API_KEY"),
        api_key=api_key
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    generated_content = chat_completion.choices[0].message.content.strip()
    print(generated_content)
    return generated_content

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            return render(request,'login.html',{'error':'Invalid username or password'})
    return render(request,'login.html')

def user_signup(request):
    if request.method == 'POST':
        username =  request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'User already exsists'
                return render(request,'signup.html',{'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html',{'error_message':error_message})

    return render(request,'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')




def blog_list(request):
    blog_articles = BlogPost.objects.filter(user = request.user)
    return render(request,'all-blogs.html', {'blog_articles':blog_articles})

def blog_details(request,pk):
    blog_article = BlogPost.objects.get(id=pk)
    if request.user == blog_article.user:
        return render(request,'blog-details.html',{'blog_article':blog_article})
    else:
        return redirect('/')