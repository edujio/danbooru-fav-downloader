import requests
from requests.auth import HTTPBasicAuth
from string import Template
import pathlib
import os
from datetime import datetime
import hashlib
import errno

has_posts = True
current_page = 1
url_template = Template('https://danbooru.donmai.us/posts.json?page=$current_page&tags=ordfav:$username')
directory = str(pathlib.Path(__file__).parent.absolute())
create_dir = True

username = None
api_key = None

def query_answer(question, default="no"):
    valid = { 'yes': True, 'ye': True, 'y': True, 'Y': True,
              'no': False, 'n': False, 'N': False }

    while True:
        print(question, '[y/N] ')
        choice = input().lower()

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print('Please respond with \'yes\' or \'no\'' \
                             '(or \'y\' or \'n\').')

def md5_check(file_path, md5):
        calculated_md5 = hashlib.md5()

        calculated_filesize = os.stat(file_path).st_size
        
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(5242880)
                if chunk:
                    calculated_md5.update(chunk)
                else:
                    break
        calculated_md5 = calculated_md5.hexdigest()
        
        return calculated_md5 == md5

username = input('What is your username? ')

if query_answer('If you have made private your favorite posts, or have some posts that are only visible to Gold members and up,' \
                'you will need to authenticate by providing the API Key for your username. ' \
                'The API Key is gonna be stored in memory during the script execution. ' \
                'It won\'t be stored anywhere else. Do you want to input your API Key?'):
    api_key = input('Please insert your API Key: ')

directory = os.path.join(directory, f'{username}\'s-favorites-{datetime.today().strftime("%Y-%m-%d-%H:%M:%S")}')

while has_posts:
    try:
        if api_key != None:
            page = requests.get(url_template.substitute(username=username, current_page=current_page), auth=HTTPBasicAuth(username, api_key))
        else:
            page = requests.get(url_template.substitute(username=username, current_page=current_page))

        if page.json() != []:
            response = page.json()

            if 'success' in response and response['success'] == False:
                print('Failed to get a response. Did you write your username/API Key right?')
                has_posts = False
            else:
                print(f'Current Page: {current_page}')

                if not os.path.exists(directory) and create_dir:
                    os.mkdir(directory)
                    create_dir = False

                for post in response:
                    if 'file_url' not in post:
                        print('Cound not download file. URL missing. This usually happens when you\'re not authenticated to see a post. ' \
                              'Please restart the script and provide the API Key for your account to download this file.')
                    else:
                        post_file = requests.get(post['file_url'], stream=True)
                        file_path = os.path.join(directory, f'{str(post["id"])}.{post["file_ext"]}')
                        
                        with open(file_path, 'wb') as file:
                            for chunk in post_file.iter_content(chunk_size=5242880):
                                file.write(chunk)
                        
                        if not md5_check(file_path, post['md5']):
                            os.rename(file_path, os.path.join(directory, f'md5-mismatch-{str(post["id"])}.{post["file_ext"]}'))

                current_page += 1
        else:
            print('Done. End of pages.')
            has_posts = False
    
    except requests.exceptions.RequestException:
        print('Failed to get a response from the Danbooru server.')
        has_posts = False
    
    except OSError as e:
        if e.errno == errno.EACCES:
            print('Permission denied when creating the files. Please verify if you have the right permissions on this directory.')
        has_posts = False
        
print('Done.')