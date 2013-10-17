'''
#=============================================================================
#     FileName: read_db.py
#         Desc: read baicizhan db folder, create database file for giveaword
#      Version: 1.0.0
#=============================================================================
'''
import sqlite3
import json
import os, glob

# Convert .baicizhan file to .jpg
#for file in glob.glob('./cropped_images/*.baicizhan'):
#    os.rename(file, file.replace('.baicizhan', '.jpg'))

# Read baicizhantopic.db
T_TOPIC = 0
T_UPDATEDATE = 1
T_WORD = 2
T_SENTENCE = 3
T_WORDVIDEO = 4
T_SENTENCEVIDEO = 5
T_IMAGEPATH = 6
T_THUMBIMAGEPATH = 7
T_SENTENCETRANS = 7
T_PHONETIC = 8
T_WORDMEAN = 9
T_WORDVARIANTS = 10
T_ATTROPTIONS = 11

word_list = []
conn = sqlite3.connect('baicizhantopic.db')
cs = conn.cursor()
cs.execute('select * from ZTOPICRESOURCE;')
word_info = cs.fetchone()
while word_info != None:
    word_list.append(list(word_info))
    word_info = cs.fetchone()
conn.close()

# Read baicizhantopicwordmean.db
P_TOPIC = 0
P_KEYWORDVARIANTS = 7
P_SENTENCETRANS = 8

conn = sqlite3.connect('baicizhantopicwordmean.db')
cs = conn.cursor()
cs.execute('select * from ZTOPICRESOURCEWORDEXTRA;')
additional_info = cs.fetchone()
while additional_info != None:
    for item in word_list:
        if item[T_TOPIC] == additional_info[P_TOPIC]:
            item[T_SENTENCETRANS] = additional_info[P_SENTENCETRANS]
            if additional_info[P_KEYWORDVARIANTS] != '':
                item[T_WORDVARIANTS] += (',' + additional_info[P_KEYWORDVARIANTS])
            item[T_WORDVARIANTS] = set(item[T_WORDVARIANTS].split(','))
            break;
    additional_info = cs.fetchone()
conn.close()

# Write html file
#os.rename('cropped_images', 'images')
alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
with open('book.html', mode='w', encoding='utf-8') as file:
    file.write('<html><body><table border="0">\n')
    file.write('<meta http-equiv="Content-Type" content="text/html"; charset="utf-8"/>\n')
    for word in word_list:
        image_path = './images/{}.{}'.format(word[T_WORD], word[T_IMAGEPATH].rsplit('.', 1)[1]);
        try:
            os.rename('.{}jpg'.format(word[T_IMAGEPATH].replace('cropped_', '').rstrip(alphabet)), image_path)
        except OSError:
            print('[FAILED] {} -> {}'.format(word[T_IMAGEPATH].replace('/cropped_images', './images'), image_path))
        file.write('<tr>\n')
        file.write('<td align="center" width="310"><img src="{}"></td>'.format(image_path))
        file.write('<td align="left" width="400">{} {} {}</p><例> {} {}'.format(
            word[T_WORD], word[T_PHONETIC], word[T_WORDMEAN], word[T_SENTENCE], word[T_SENTENCETRANS]))
        have_variant = False
        for variant in word[T_WORDVARIANTS]:
            if variant != word[T_WORD]:
                if not have_variant:
                    file.write('</p><变式> {}'.format(variant))
                    have_variant = True
                else:
                    file.write(', {}'.format(variant))
        attr_options = json.loads(word[T_ATTROPTIONS])
        if  len(attr_options[0]['attr_value']) > 0 and 'word_etyma_desc' in attr_options[0]['attr_value'][0].keys():
            file.write('</p><词源> {}'.format(attr_options[0]['attr_value'][0]['word_etyma_desc']))
        file.write('</td>\n')
        file.write('</tr>\n')
    file.write('</table></body></html>')

