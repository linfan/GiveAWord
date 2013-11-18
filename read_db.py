'''
#=============================================================================
#     FileName: read_db.py
#         Desc: read baicizhan db folder, create resource files for giveaword
#      Version: 3.1.0
#=============================================================================
'''

import sqlite3
import json
import os, glob, shutil
import re

# word list
word_list = []

# valid character for postfix
alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'

# ZTOPICRESOURCE table index
T_TOPIC = 0
T_UPDATEDATE = 1
T_WORDMEAN_EN = 1
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
T_ETYMA = 11
T_DEFORMATION_IMG = 12
T_DEFORMATION_DESC = 13
T_ALTEREXAMPLE = 14

# ZTOPICRESOURCEWORDEXTRA table index
P_TOPIC = 0
P_UPDATELABEL = 1
P_WORDMEAN_EN = 2
P_EXAMPLE = 3
P_ETYMA = 4
P_DEFORMATION_IMG = 5
P_DEFORMATION_DESC = 6
P_VARIANTS = 7
P_SENTENCE_TRANS = 8

# Read baicizhantopic.db
def read_baicizhantopic_db():
    conn = sqlite3.connect('baicizhantopic.db')
    cs = conn.cursor()
    cs.execute('select * from ZTOPICRESOURCE;')
    word_info = cs.fetchone()
    while word_info != None:
        item = list(word_info)
        item.extend(['', '', '']) # add two blank index
        item[T_WORDVIDEO] = item[T_WORDVIDEO].replace('.dat', '.mp3')
        item[T_SENTENCEVIDEO] = item[T_SENTENCEVIDEO].replace('.dat', '.mp3')
        word_list.append(item)
        word_info = cs.fetchone()
    conn.close()

# Read baicizhantopicwordmean.db
def read_baicizhantopicwordmean_db():
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
                item[T_ALTEREXAMPLE] = additional_info[P_EXAMPLE]
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

# Create folder
def create_folder(folder):
    try:
        os.mkdir(folder)
    except OSError or FileExistsError:
        print('[OMIT] folder {} already exist.'.format(folder))
        return False
    return True

# Copy files
def copy_files(folder, word, field):
    target_path = './{}/{}.{}'.format(folder, word[T_WORD], word[field].rsplit('.', 1)[1]).replace(' ', '_');
    try:
        shutil.copy('.{}baicizhan'.format(word[field].rstrip(alphabet)), target_path)
    except OSError:
        print('[FAILED] {} -> {}'.format(word[field], target_path))

# Convert dictionary resource
def convert_dict_recource():
    if create_folder('book/book_images'):
        for word in word_list: # copy image file
            copy_files('book/book_images', word, T_IMAGEPATH)
    if create_folder('book/book_pronounce'):
        for word in word_list: # copy word pronounce file
            copy_files('book/book_pronounce', word, T_WORDVIDEO)
    if create_folder('book/book_sentence'):
        for word in word_list: # copy sentence pronounce file
            copy_files('book/book_sentence', word, T_SENTENCEVIDEO)
    if create_folder('book/book_deformation'):
        for word in word_list: # copy deformation image file
            if word[T_DEFORMATION_IMG]: 
                copy_files('book/book_deformation', word, T_DEFORMATION_IMG)

# Write html file
def write_html_file():
    with open('book/book.html', mode='w', encoding='utf-8') as file:
        file.write('<html><body><table cellSpacing="4" border="0">\n')
        file.write('<meta http-equiv="Content-Type" content="text/html"; charset="utf-8"/>\n')
        for word in word_list:
            
            # first row
            file.write('<tr>\n')
            # first column
            target_path = './book_images/{}.{}'.format(word[T_WORD], 
                    word[T_IMAGEPATH].rsplit('.', 1)[1]).replace(' ', '_');
            file.write('<td align="center" valign="top" width="150" rowSpan="3">')
            file.write('<img width="90%" height="auto" src="{}"></td>\n'.format(target_path))
            # second column
            file.write('<td align="left" width="400"><font size="3"><b>{}</b></font> <font size="2">{} {}</font></td>'.format(
                word[T_WORD], word[T_PHONETIC], word[T_WORDMEAN]))
#            if word[T_WORDMEAN_EN]:
#                file.write('<br><英译> {}'.format(word[T_WORDMEAN_EN]))
            # third column
            file.write('<td align="left" valign="middle" width="150" rowSpan="3">')
            if word[T_DEFORMATION_IMG]:
                target_path = './book_deformation/{}.{}'.format(word[T_WORD], 
                        word[T_DEFORMATION_IMG].rsplit('.', 1)[1]).replace(' ', '_');
                file.write('<img width="90%" height="auto" src="{}">'.format(target_path))
                if word[T_DEFORMATION_DESC]:
                    file.write('<br><font size="2">{}</font>'.format(word[T_DEFORMATION_DESC]))
            file.write('</td>\n')
            file.write('</tr>\n')

            # second row
            file.write('<tr>\n')
            file.write('<td align="left" valign="top" width="400"><font size="2"><例> {} {}</font></td>\n'
                    .format('<u><b>{}</b></u>'.format(word[T_WORD])
                    .join(re.split(word[T_WORD], word[T_SENTENCE], flags = re.IGNORECASE)), word[T_SENTENCETRANS]))
            file.write('</tr>\n')

            # third row
            file.write('<tr>\n')
            file.write('<td align="left" valign="top" width="400"><font size="2">')
            have_variant = False
            have_etyma = False
            if word[T_ETYMA]:
                file.write('<词源> {}'.format(word[T_ETYMA]))
                have_etyma = True
            for variant in word[T_WORDVARIANTS]:
                if variant != word[T_WORD]:
                    if not have_variant:
                        if have_etyma:
                            file.write(' ')
                        file.write('<变式> {}'.format(variant))
                        have_variant = True
                    else:
                        file.write(', {}'.format(variant))
            file.write('</font></td>\n')
            file.write('</tr>\n')

        file.write('</table></body></html>')

def generate_word_book():
    read_baicizhantopic_db()
    read_baicizhantopicwordmean_db()
    print('total {} words.'.format(len(word_list)))
    create_folder('book')
    convert_dict_recource()
    write_html_file()

if __name__ == '__main__':
    generate_word_book()

