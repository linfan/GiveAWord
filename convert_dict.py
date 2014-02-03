'''
#=============================================================================
#     FileName: convert_dict.py
#         Desc: read baicizhan db folder, create database and resource file for giveaword
#      Version: 2.3.0
#=============================================================================
'''

import sqlite3
import json
import os, glob, shutil
import sys
import re
from optparse import OptionParser

# Global constant
APP_VERSION = 2.3

# Global variable
options = None

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
def read_baicizhantopic_db(src_folder):
    database_path = src_folder + os.sep + 'baicizhantopic.db'
    print('Reading database: {}'.format(database_path))
    conn = sqlite3.connect(database_path)
    cs = conn.cursor()
    cs.execute('select * from ZTOPICRESOURCE;')
    word_info = cs.fetchone()
    while word_info != None:
        item = list(word_info)
        item.extend(['', '', '']) # add 3 blank fields
        word_list.append(item)
        word_info = cs.fetchone()
    conn.close()

# Modify resource path to the real destination
def transform_resource_path():
    for item in word_list:
        item[T_IMAGEPATH] = './dict_images/{}.{}'.format( item[T_WORD].replace(' ', '_').replace(os.sep, '_@_'),
                item[T_IMAGEPATH].rsplit('.', 1)[1])
        item[T_WORDVIDEO] = './dict_pronounce/{}.{}'.format( item[T_WORD].replace(' ', '_').replace(os.sep, '_@_'), '.mp3')
        item[T_SENTENCEVIDEO] = './dict_sentence/{}.{}'.format( item[T_WORD].replace(' ', '_').replace(os.sep, '_@_'), '.mp3')
        if item[T_DEFORMATION_IMG]:
            item[T_DEFORMATION_IMG] = './dict_deformation/{}.{}'.format(item[T_WORD].replace(' ', '_').replace(os.sep, '_@_'),
                item[T_DEFORMATION_IMG].rsplit('.', 1)[1])

# Read baicizhantopicwordmean.db
def read_baicizhantopicwordmean_db(src_folder):
    database_path = src_folder + os.sep + 'baicizhantopicwordmean.db'
    print('Reading database: {}'.format(database_path))
    conn = sqlite3.connect(database_path)
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
                item[T_WORDVARIANTS] = ' '.join(set(item[T_WORDVARIANTS].split(',')))
                break;
        additional_info = cs.fetchone()
    conn.close()

# Create folder, report to teminate if folder already exist
def create_folder(folder, suppressError):
    try:
        os.mkdir(folder)
        print('[INFO] folder {} created.'.format(folder))
    except OSError or FileExistsError:
        if suppressError:
            print('[INFO] entering folder {}.'.format(folder))
        else:
            print('[OMIT] folder {} already exist.'.format(folder))
        return False
    return True

# Copy image file
def copy_image(src_folder, dst_folder, word, field):
    source_path = '{}{}baicizhan'.format(src_folder, word[field].rstrip(alphabet))
    target_path = './{}/{}.{}'.format(dst_folder,
            word[T_WORD].replace(' ', '_').replace(os.sep, '_@_'), word[field].rsplit('.', 1)[1])
    copy_file(source_path, target_path)

# Copy audio file
def copy_audio(src_folder, dst_folder, word, field):
    source_path = '{}{}baicizhan'.format(src_folder, word[field].rstrip(alphabet))
    target_path = './{}/{}.{}'.format(dst_folder,
            word[T_WORD].replace(' ', '_').replace(os.sep, '_@_'), 'mp3')
    copy_file(source_path, target_path)

# Copy file, report to teminate if target already exist
def copy_file(source_path, target_path):
    try:
        shutil.copy(source_path, target_path)
    except (OSError, IOError):
        print('[FAIL] {} -> {}'.format(source_path, target_path))
        print(sys.exc_info()[0],sys.exc_info()[1])

# Convert dictionary resource
def convert_dict_recource(src_folder):
    global options
    # copy image file
    if create_folder('dict_images', options.optAppendMode) or options.optAppendMode:
        for word in word_list:
            copy_image(src_folder, 'dict_images', word, T_IMAGEPATH)
    # copy word pronounce file
    if create_folder('dict_pronounce', options.optAppendMode) or options.optAppendMode:
        for word in word_list:
            copy_audio(src_folder, 'dict_pronounce', word, T_WORDVIDEO)
    # copy sentence pronounce file
    if create_folder('dict_sentence', options.optAppendMode) or options.optAppendMode:
        for word in word_list:
            copy_audio(src_folder, 'dict_sentence', word, T_SENTENCEVIDEO)
    # copy deformation image file
    if create_folder('dict_deformation', options.optAppendMode) or options.optAppendMode:
        for word in word_list:
            if word[T_DEFORMATION_IMG]:
                copy_image(src_folder, 'dict_deformation', word, T_DEFORMATION_IMG)

def is_table_exist(cursor, table_name):
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' and name='{}';".format(table_name))
    return (cursor.fetchone()[0] != 0)

def write_word_db():
    global options
    conn = sqlite3.connect('dict.db')
    cs = conn.cursor()
    if (not options.optAppendMode) and is_table_exist(cs, 'DICT'):
        cs.execute("DROP TABLE DICT")
    if not is_table_exist(cs, 'DICT'):
        cs.execute("CREATE TABLE DICT (WORD VARCHAR PRIMARY KEY, PHONETIC VARCHAR, WORDMEAN VARCHAR, WORDMEANTRANS VARCHAR, SENTENCE VARCHAR, SENTENCETRANS VARCHAR, WORDVARIANTS VARCHAR, ETYMA VARCHAR, ALTEREXAMPLE VARCHAR, SENTENCEIMAGE VARCHAR, DEFORMATIONIMG VARCHAR, DEFORMATIONDESC VARCHAR, PRONOUNCEAUDIO VARCHAR, SENTENCEAUDIO VARCHAR, UPDATEDATE INTEGER, SCORE INTEGER, CORRECTANSWERTIMES INTEGER, WRONGANSWERTIMES INTEGER, REPEATTHISTIME INTEGER);")
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
        command = "INSERT OR REPLACE INTO DICT VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}, {});".format(
                item[D_WORD], item[D_PHONETIC], item[D_WORDMEAN], item[D_WORDMEANTRANS], item[D_SENTENCE],
                item[D_SENTENCETRANS], item[D_WORDVARIANTS], item[D_ETYMA], item[D_ALTEREXAMPLE],
                item[D_SENTENCEIMAGE], item[D_DEFORMATIONIMG], item[D_DEFORMATIONDESC], item[D_PRONOUNCEAUDIO],
                item[D_SENTENCEAUDIO], item[D_UPDATEDATE], item[D_SCORE], item[D_CORRECTANSWERTIMES],
                item[D_WRONGANSWERTIMES], item[D_REPEATTHISTIME])
        try:
            cs.execute(command)
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            print("[ERROR] " + command)
            print(sys.exc_info()[0],sys.exc_info()[1])
            break
    if (not options.optAppendMode) and is_table_exist(cs, 'INFO'):
        cs.execute("DROP TABLE INFO")
    if not is_table_exist(cs, 'INFO'):
        cs.execute("CREATE TABLE INFO (USER VARCHAR, LASTUSETIME INTEGER, STUDYREVIEWBALANCE INTEGER);")
        cs.execute("INSERT INTO INFO VALUES('LIN', 0, 0);")
    conn.commit()
    conn.close()

def generate_word_db():
    global options
    # baicizhan dictionary folder
    src_folder = '.'
    parser = OptionParser(version="%prog v{}".format(APP_VERSION),
            usage="Usage: %prog [options] [baicizhan_folder]\nTry '%prog --help' for more options")
    parser.set_defaults(optAppendMode = False)
    parser.add_option("-a", "--append", dest="optAppendMode",
            action="store_true", help="Append new words into current dictionary")
    (opts, args) = parser.parse_args()
    options = opts
    if args:
        src_folder = args[0].rstrip(os.sep)
    print('Reading dictionary from {}/ folder..'.format(src_folder))
    read_baicizhantopic_db(src_folder)
    read_baicizhantopicwordmean_db(src_folder)
    print('total {} words.'.format(len(word_list)))
    convert_dict_recource(src_folder)
    transform_resource_path()
    write_word_db()

if __name__ == '__main__':
    generate_word_db()

