'''
#=============================================================================
#     FileName: create_dict.py
#         Desc: read baicizhan db folder, create database and resource file for giveaword
#      Version: 2.1.0
#=============================================================================
'''

import sqlite3
import json
import os, glob, shutil
import sys
import re

# word list
word_list = []
word_dict = []

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

# DICT table index
D_WORD = 0
D_PHONETIC = 1
D_WORDMEAN = 2
D_WORDMEANTRANS = 3
D_SENTENCE = 4
D_SENTENCETRANS = 5
D_WORDVARIANTS = 6
D_ETYMA = 7
D_ALTEREXAMPLE = 8
D_SENTENCEIMAGE = 9
D_DEFORMATIONIMG = 10
D_DEFORMATIONDESC = 11
D_PRONOUNCEAUDIO = 12
D_SENTENCEAUDIO = 13
D_UPDATEDATE = 14
D_SCORE = 15
D_CORRECTANSWERTIMES = 16
D_WRONGANSWERTIMES = 17
D_REPEATTHISTIME = 18

# Read baicizhantopic.db
def read_baicizhantopic_db():
    conn = sqlite3.connect('baicizhantopic.db')
    cs = conn.cursor()
    cs.execute('select * from ZTOPICRESOURCE;')
    word_info = cs.fetchone()
    while word_info != None:
        item = list(word_info)
        item.extend(['', '', '']) # add two blank index
        item[T_IMAGEPATH] = './book_images/{}.{}'.format(
                item[T_WORD], item[T_IMAGEPATH].rsplit('.', 1)[1]).replace(' ', '_');
        item[T_WORDVIDEO] = item[T_WORDVIDEO].replace('.dat', '.mp3')
        item[T_WORDVIDEO] = './book_pronounce/{}.{}'.format(
                item[T_WORD], item[T_WORDVIDEO].rsplit('.', 1)[1]).replace(' ', '_');
        item[T_SENTENCEVIDEO] = item[T_SENTENCEVIDEO].replace('.dat', '.mp3')
        item[T_SENTENCEVIDEO] = './book_sentence/{}.{}'.format(
                item[T_WORD], item[T_SENTENCEVIDEO].rsplit('.', 1)[1]).replace(' ', '_');
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
                if item[T_DEFORMATION_IMG]:
                    item[T_DEFORMATION_IMG] = './book_deformation/{}.{}'.format(item[T_WORD],
                        item[T_DEFORMATION_IMG].rsplit('.', 1)[1]).replace(' ', '_');
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
                item[T_WORDVARIANTS] = ' '.join(set(item[T_WORDVARIANTS].split(',')))
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

def is_table_exist(cursor, table_name):
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' and name='{}';".format(table_name))
    return (cursor.fetchone()[0] != 0)

def write_word_db():
    conn = sqlite3.connect('dict.db')
    cs = conn.cursor()
    if is_table_exist(cs, 'DICT'):
        cs.execute("DROP TABLE DICT")
    cs.execute("CREATE TABLE DICT (WORD VARCHAR, PHONETIC VARCHAR, WORDMEAN VARCHAR, WORDMEANTRANS VARCHAR, SENTENCE VARCHAR, SENTENCETRANS VARCHAR, WORDVARIANTS VARCHAR, ETYMA VARCHAR, ALTEREXAMPLE VARCHAR, SENTENCEIMAGE VARCHAR, DEFORMATIONIMG VARCHAR, DEFORMATIONDESC VARCHAR, PRONOUNCEAUDIO VARCHAR, SENTENCEAUDIO VARCHAR, UPDATEDATE INTEGER, SCORE INTEGER, CORRECTANSWERTIMES INTEGER, WRONGANSWERTIMES INTEGER, REPEATTHISTIME INTEGER);")
    for item in word_list:
        word = []
        word.append(item[T_WORD].replace("'","''"))
        word.append(item[T_PHONETIC] and item[T_PHONETIC].lstrip("\xa0").replace("'","''") or 'NULL')
        word.append(item[T_WORDMEAN_EN] and item[T_WORDMEAN_EN].replace("'","''") or 'NULL')
        word.append(item[T_WORDMEAN] and item[T_WORDMEAN].replace("'","''") or 'NULL')
        word.append(item[T_SENTENCE] and item[T_SENTENCE].replace("'","''") or 'NULL')
        word.append(item[T_SENTENCETRANS] and item[T_SENTENCETRANS].replace("'","''") or 'NULL')
        word.append(item[T_WORDVARIANTS] and item[T_WORDVARIANTS].replace("'","''") or 'NULL')
        word.append(item[T_ETYMA] and item[T_ETYMA].replace("'","''") or 'NULL')
        word.append(item[T_ALTEREXAMPLE] and item[T_ALTEREXAMPLE].replace("'","''") or 'NULL')
        word.append(item[T_IMAGEPATH] and item[T_IMAGEPATH].replace("'","''") or 'NULL')
        word.append(item[T_DEFORMATION_IMG] and item[T_DEFORMATION_IMG].replace("'","''") or 'NULL')
        word.append(item[T_DEFORMATION_DESC] and item[T_DEFORMATION_DESC].replace("'","''") or 'NULL')
        word.append(item[T_WORDVIDEO] and item[T_WORDVIDEO].replace("'","''") or 'NULL')
        word.append(item[T_SENTENCEVIDEO] and item[T_SENTENCEVIDEO].replace("'","''") or 'NULL')
        word.append(0)
        word.append(0)
        word.append(0)
        word.append(0)
        word.append(0)
        word_dict.append(word)
    for item in word_dict:
        command = "INSERT INTO DICT VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}, {});".format(
                item[D_WORD], item[D_PHONETIC], item[D_WORDMEAN], item[D_WORDMEANTRANS], item[D_SENTENCE],
                item[D_SENTENCETRANS], item[D_WORDVARIANTS], item[D_ETYMA], item[D_ALTEREXAMPLE],
                item[D_SENTENCEIMAGE], item[D_DEFORMATIONIMG], item[D_DEFORMATIONDESC], item[D_PRONOUNCEAUDIO],
                item[D_SENTENCEAUDIO], item[D_UPDATEDATE], item[D_SCORE], item[D_CORRECTANSWERTIMES],
                item[D_WRONGANSWERTIMES], item[D_REPEATTHISTIME])
        try:
            cs.execute(command)
        except sqlite3.OperationalError:
            print(sys.exc_info()[0],sys.exc_info()[1])
            print("[ERROR] " + command)
            break
    if is_table_exist(cs, 'INFO'):
        cs.execute("DROP TABLE INFO")
    cs.execute("CREATE TABLE INFO (USER VARCHAR, LASTUSETIME INTEGER, STUDYREVIEWBALANCE INTEGER);")
    cs.execute("INSERT INTO INFO VALUES('LIN', 0, 0);")
    conn.commit()
    conn.close()

def generate_word_db():
    read_baicizhantopic_db()
    read_baicizhantopicwordmean_db()
    print('total {} words.'.format(len(word_list)))
    write_word_db()
    create_folder('book')
    convert_dict_recource()

if __name__ == '__main__':
    generate_word_db()

