'''
#=============================================================================
#     FileName: read_db.py
#         Desc: read baicizhan db folder, create database file for giveaword
#      Version: 2.0.0
#=============================================================================
'''
import sqlite3
import json
import os, glob, shutil

# Read baicizhantopic.db
T_TOPIC = 0
T_UPDATEDATE = 1
T_WORDMEAN_EN = 1
T_WORD = 2
T_SENTENCE = 3
T_WORDVIDEO = 4
T_DEFORMATION_IMG = 4
T_SENTENCEVIDEO = 5
T_DEFORMATION_DESC = 5
T_IMAGEPATH = 6
T_THUMBIMAGEPATH = 7
T_SENTENCETRANS = 7
T_PHONETIC = 8
T_WORDMEAN = 9
T_WORDVARIANTS = 10
T_ATTROPTIONS = 11
T_ETYMA = 11

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
P_UPDATELABEL = 1
P_WORDMEAN_EN = 2
P_EXAMPLE = 3
P_ETYMA = 4
P_DEFORMATION_IMG = 5
P_DEFORMATION_DESC = 6
P_VARIANTS = 7
P_SENTENCE_TRANS = 8

conn = sqlite3.connect('baicizhantopicwordmean.db')
cs = conn.cursor()
cs.execute('select * from ZTOPICRESOURCEWORDEXTRA;')
additional_info = cs.fetchone()
while additional_info != None:
    for item in word_list:
        if item[T_TOPIC] == additional_info[P_TOPIC]:
            item[T_SENTENCETRANS] = additional_info[P_SENTENCE_TRANS]
            item[T_DEFORMATION_IMG] = additional_info[P_DEFORMATION_IMG]
            item[T_DEFORMATION_DESC] = additional_info[P_DEFORMATION_DESC]
            item[T_WORDMEAN_EN] = additional_info[P_WORDMEAN_EN]
            attr_options = json.loads(item[T_ATTROPTIONS])
            if len(attr_options[0]['attr_value']) > 0 and 'word_etyma_desc' in attr_options[0]['attr_value'][0].keys():
                item[T_ETYMA] = attr_options[0]['attr_value'][0]['word_etyma_desc']
            elif additional_info[P_ETYMA]:
                item[T_ETYMA] = additional_info[P_ETYMA]
            else:
                item[T_ETYMA] = None
            if additional_info[P_VARIANTS] != '':
                item[T_WORDVARIANTS] += (',' + additional_info[P_VARIANTS])
            item[T_WORDVARIANTS] = set(item[T_WORDVARIANTS].split(','))
            break;
    additional_info = cs.fetchone()
conn.close()

print('total {} words.'.format(len(word_list)))

# Write html file
os.mkdir('images')
os.mkdir('deformation')
alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
with open('book.html', mode='w', encoding='utf-8') as file:
    file.write('<html><body><table border="0">\n')
    file.write('<meta http-equiv="Content-Type" content="text/html"; charset="utf-8"/>\n')
    for word in word_list:
        file.write('<tr>\n')

        # first column
        image_path = './images/{}.{}'.format(word[T_WORD], word[T_IMAGEPATH].rsplit('.', 1)[1]);
        try:
            shutil.copy('.{}baicizhan'.format(word[T_IMAGEPATH].rstrip(alphabet)), image_path)
        except OSError:
            print('[FAILED] {} -> {}'.format(word[T_IMAGEPATH], image_path))
        file.write('<td align="center" width="310"><img src="{}"></td>\n'.format(image_path))

        # second column
        file.write('<td align="left" width="400">{} {} {}</p><例> {} {}'.format(
            word[T_WORD], word[T_PHONETIC], word[T_WORDMEAN], word[T_SENTENCE], word[T_SENTENCETRANS]))
        if word[T_WORDMEAN_EN]:
            file.write('</p><英译> {}'.format(word[T_WORDMEAN_EN]))
        have_variant = False
        for variant in word[T_WORDVARIANTS]:
            if variant != word[T_WORD]:
                if not have_variant:
                    file.write('</p><变式> {}'.format(variant))
                    have_variant = True
                else:
                    file.write(', {}'.format(variant))
        if word[T_ETYMA]:
            file.write('</p><词源> {}'.format(word[T_ETYMA]))
        file.write('</td>\n')

        # third column
        file.write('<td align="left" width="310">')
        if word[T_DEFORMATION_IMG]:
            image_path = './deformation/{}.{}'.format(word[T_WORD], word[T_DEFORMATION_IMG].rsplit('.', 1)[1]);
            try:
                shutil.copy('.{}baicizhan'.format(word[T_DEFORMATION_IMG].rstrip(alphabet)), image_path)
            except OSError:
                print('[FAILED] {} -> {}'.format(word[T_DEFORMATION_IMG], image_path))
            file.write('<img src="{}">'.format(image_path))
            if word[T_DEFORMATION_DESC]:
                file.write('<\p>{}'.format(word[T_DEFORMATION_DESC]))
        file.write('</td>\n')

        file.write('</tr>\n')
    file.write('</table></body></html>')

