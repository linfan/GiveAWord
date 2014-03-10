GiveAWord
=========

A simple program for lookup English words and learn English words

 - convert_dict.py - generate dictionary and resource (image and audio) files from data of a BaiCiZhan folder
 - giveaword.py    - lookup a English word / Chinese word, or let you guess a English word by giving its meanning

The application use "eog" and "mpg123" to open word image and play pronunciation audios, the apps can be modified by edit below lines at the begin of giveaword.py:
<pre>
IMAGE_APP = 'eog'
AUDIO_APP = 'mpg123'
</pre>

A sample dictionary I generated using all 18 dictionarys of Baicizhan app, at Aug, 2013 can be download from below link:<br>
http://pan.baidu.com/s/1c048KFI <br>
This dictionary size after decompress is 1.2GB, contenting 15602 English words, include coorsponding images and pronunciation audios.
