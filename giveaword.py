'''
#=============================================================================
#     FileName: giveaword.py
#      Version: 2.3.0
#=============================================================================
'''
import sqlite3
import time
import sys, re, os, signal
from optparse import OptionParser

# Global constant
APP_VERSION = 2.3
BALANCE_LOW_LEVEL = -9
BALANCE_HIGH_LEVEL = 5
MAXIMUM_REVIEW_TIME = 99
BULK_LOOKUP_PAGE_SIZE = 5

# Global variable
db_conn = None
db_cursor = None
options = None
user_info = None

# Database file
WORK_DIR = sys.path[0]
DICT_DB = (WORK_DIR + '/dict.db')
DICT_TABLE = 'DICT'
INFO_TABLE = 'INFO'

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

# INFO table index
I_USER = 0
I_LASTUSETIME = 1
I_STUDYREVIEWBALANCE = 2

# Alternative charactor unprintable phonetic symbol
PHONETIC_MAP = { '\u00E6':'@', '\u00F0':'6', '\u014B':'n', '\u0251':'a', '\u0252':'o',
    '\u0254':'o', '\u0259':'3', '\u025B':'E', '\u025C':'3', '\u0261':'g', '\u026A':'I',
    '\u0283':'S', '\u028A':'U', '\u028C':'^', '\u0292':'J', '\u02C8':'\'', '\u02CC':',',
    '\u02D0':':', '\u03B8':'0' }

# For word auto-complete
# WORD PHONETIC WORDMEAN WORDMEANTRANS SENTENCE SENTENCETRANS WORDVARIANTS
# ETYMA UPDATEDATE SCORE CORRECTANSWERTIMES WRONGANSWERTIMES REPEATTHISTIME
# ALTEREXAMPLE SENTENCEIMAGE DEFORMATIONIMG DEFORMATIONDESC PRONOUNCEAUDIO
# SENTENCEAUDIO USER LASTUSETIME STUDYREVIEWBALANCE

# Utility functions

def elegantExit():
    ''' Close database and exit '''
    closeDictDb()
    sys.exit(-1)

def ret1or2():
    ''' Reture 1 or 2 '''
    return (int(time.time() * 100) % 2) and 1 or 2

# Database operations

def openDictDb():
    ''' Open DICT database '''
    global db_conn, db_cursor, user_info
    if not db_conn:
        db_conn = sqlite3.connect(DICT_DB)
        db_cursor = db_conn.cursor()
        if not db_cursor:
            raise Exception("Open database failed !")
        user_info = getUserInfo()
        if user_info[I_LASTUSETIME] != 0 and time.time() - user_info[I_LASTUSETIME] > (3600 * 5):
            user_info[I_STUDYREVIEWBALANCE] = BALANCE_LOW_LEVEL

def closeDictDb():
    ''' Close DICT database '''
    global db_conn, user_info
    if db_conn:
        db_cursor.execute("UPDATE {} SET LASTUSETIME = {}, STUDYREVIEWBALANCE = {} WHERE USER = 'LIN';".format(
            INFO_TABLE, int(time.time()), user_info[I_STUDYREVIEWBALANCE]))
        db_conn.commit()
        db_conn.close()
        db_conn = None

def getUserInfo():
    ''' Get information in INFO table '''
    global db_cursor
    db_cursor.execute("SELECT * FROM {} WHERE USER = 'LIN';".format(INFO_TABLE))
    return nextRecord()

def searchDb(condition, order = None):
    ''' Do select operation in DICT database '''
    global db_cursor
    if order:
        command = "SELECT * FROM {} WHERE {} ORDER BY {};".format(DICT_TABLE, condition, order)
    else:
        command = "SELECT * FROM {} WHERE {};".format(DICT_TABLE, condition)
    try:
        if options.optShowRawRecord:
            print('[DEBUG] {}'.format(command))
        db_cursor.execute(command)
    except sqlite3.OperationalError:
        print(sys.exc_info()[0],sys.exc_info()[1])
        print("[ERROR] " + command)

def searchAllRecordFromDb(condition, order = None):
    ''' Find all the records meet the condition '''
    global db_cursor
    searchDb(condition, order)
    return db_cursor.fetchall()

def nextRecord():
    ''' Find the next record meet the condition '''
    global options, db_cursor
    record = db_cursor.fetchone()
    if options.optShowRawRecord:
        if record:
            print('[DEBUG]', end = ' ')
            print(record)
        else:
            print('[DEBUG] No more record.')
    return record and list(record) or None

def searchOneRecordFromDb(condition, order = None):
    ''' Find the first record meet the condition '''
    searchDb(condition, order)
    return nextRecord()

def updateOneRecord(condition, field_value):
    ''' Update database record according to given condition '''
    command = "UPDATE {} SET {} WHERE {};".format(DICT_TABLE, field_value, condition)
    try:
        db_cursor.execute(command)
    except sqlite3.OperationalError:
        print(sys.exc_info()[0],sys.exc_info()[1])
        print("[ERROR] " + command)

# Unit functions

def showImage(filename, playOnBackground = True):
    ''' Show specific image file '''
    global options
    if options.optShowPicture:
        if playOnBackground:
            os.system('eog {}{} > /dev/null 2>&1 &'.format(WORK_DIR, filename[1:]))
        else:
            os.system('eog {}{} > /dev/null 2>&1'.format(WORK_DIR, filename[1:]))

def playAudio(filename, playOnBackground = True):
    ''' Play specific audio mp3 file '''
    global options
    if options.optPlayAudio:
        if playOnBackground:
            os.system('mpg123 {}{} > /dev/null 2>&1 &'.format(WORK_DIR, filename[1:]))
        else:
            os.system('mpg123 {}{} > /dev/null 2>&1'.format(WORK_DIR, filename[1:]))

def updateAWord(word, isCorrect, scoreDelta):
    ''' Update word's last study time and score etc. '''
    global user_info
    if user_info[I_STUDYREVIEWBALANCE] >= BALANCE_HIGH_LEVEL:
        user_info[I_STUDYREVIEWBALANCE] = BALANCE_LOW_LEVEL
    else:
        user_info[I_STUDYREVIEWBALANCE] += ret1or2()
    if isCorrect:
        updateOneRecord("WORD = '{}'".format(word[D_WORD]),
            "UPDATEDATE = {}, SCORE = {}, CORRECTANSWERTIMES = {}, WRONGANSWERTIMES = {}, REPEATTHISTIME = {}".format(
            int(time.time()), word[D_SCORE] + scoreDelta, word[D_CORRECTANSWERTIMES] + 1, word[D_WRONGANSWERTIMES], 0 ))
    else:
        updateOneRecord("WORD = '{}'".format(word[D_WORD]),
            "UPDATEDATE = {}, SCORE = {}, CORRECTANSWERTIMES = {}, WRONGANSWERTIMES = {}, REPEATTHISTIME = {}".format(
            int(time.time()), word[D_SCORE] + scoreDelta, word[D_CORRECTANSWERTIMES], word[D_WRONGANSWERTIMES] + 1, 1))

def killAWord(word):
    ''' Mark a word as known '''
    word[D_SCORE] = MAXIMUM_REVIEW_TIME

def getANewWord():
    ''' Select a new word from database to learn '''
    return searchOneRecordFromDb('UPDATEDATE = 0')

def getALearnedWord():
    ''' Select a learn word from database to review '''
    word = searchOneRecordFromDb('REPEATTHISTIME = 1', 'UPDATEDATE')
    if not word:
        word = searchOneRecordFromDb('UPDATEDATE != 0 AND SCORE < {}'.format(MAXIMUM_REVIEW_TIME), 'SCORE, UPDATEDATE')
    return word

def shouldLearnANewWord():
    ''' Judge whether it is time to learn a new word '''
    global user_info
    return (user_info[I_STUDYREVIEWBALANCE] >= 0)

def showWordSentence(word):
    ''' Show example sentence in a standard format '''
    global options
    print('[E.g.] {}'.format(word[D_SENTENCE]))
    if options.optPrintTranslation:
        print('[例] {}'.format(word[D_SENTENCETRANS]))
    showImage(word[D_SENTENCEIMAGE])
    playAudio(word[D_SENTENCEAUDIO])

def showWordPhonetic(word, endLine = True):
    ''' Show word phonetic and play pronunciation '''
    try:
        if endLine:
            print(word[D_PHONETIC])
        else:
            print(word[D_PHONETIC], end = ' ')
    except UnicodeEncodeError:
        alternativePhonetic = word[D_PHONETIC]
        for k, v in PHONETIC_MAP.items():
            alternativePhonetic = alternativePhonetic.replace(k, v)
        print(alternativePhonetic)
    playAudio(word[D_PRONOUNCEAUDIO], False)

def showWordMeaning(word):
    ''' Show word meaning in a standard format '''
    if (word[D_WORDMEAN] != 'NULL') or (options.optPrintTranslation and word[D_WORDMEANTRANS] != 'NULL'):
        if word[D_WORDMEAN] != 'NULL':
            print(word[D_WORDMEAN])
        if options.optPrintTranslation and word[D_WORDMEANTRANS] != 'NULL':
            print(word[D_WORDMEANTRANS])
    else:
        if word[D_ALTEREXAMPLE] != 'NULL':
            print('[E.g.] {}'.format(word[D_ALTEREXAMPLE]))
        else:
            print('[E.g.] {}'.format(word[D_SENTENCE]))

def showWordDeformation(word):
    ''' Show word deformation in a standard format '''
    global options
    if options.optShowPicture and word[D_DEFORMATIONIMG] != 'NULL':
        showImage(word[D_DEFORMATIONIMG])
        if word[D_DEFORMATIONDESC] != 'NULL':
            print('[Tips] {}'.format(word[D_DEFORMATIONDESC]))

def showWordBriefWithChinese(word):
    print(word[D_WORD], end = ' ')
    showWordPhonetic(word, False)
    translation = word[D_WORDMEANTRANS].replace('\n', ' ').replace('\r', '')
    print(translation)

def showWordInfo(word):
    ''' Show word information in a standard format '''
    global options
    print(word[D_WORD], end = ' ')
    showWordPhonetic(word, True)
    showWordMeaning(word)
    showWordDeformation(word)
    showWordSentence(word)
    if word[D_WORDVARIANTS] != 'NULL':
        print('[Variants] {}'.format(word[D_WORDVARIANTS]))
    if options.optPrintTranslation and word[D_ETYMA] != 'NULL':
         print('[Etyma] {}'.format(word[D_ETYMA]))

def isEnglishWord(a_str):
    for c in a_str:
        if not ((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '?' or c == '*'):
            return False
    return True

def lookUpInBulk(search_str, word_to_lookup, page):
    if page == 'all':
        word = searchOneRecordFromDb(search_str)
    elif page.isdigit():
        word = searchOneRecordFromDb('{} limit {} offset {}'.format(search_str,
            BULK_LOOKUP_PAGE_SIZE, int(page) * BULK_LOOKUP_PAGE_SIZE))
    else:
        print("[ERROR] Invalid page number.")
        return
    if word == None:
        if page == 'all':
            print("[SORRY] Word '{}' no exist in dictionary.".format(word_to_lookup))
        else:
            print("[SORRY] Page number {} of word '{}' no exist.".format(page, word_to_lookup))
    while word != None:
        showWordBriefWithChinese(word)
        word = nextRecord()

# Major functions

def lookUpAWord(letters, page = 'all'):
    ''' Main enter of looking up a word '''
    openDictDb()
    if not isEnglishWord(letters):
        lookUpInBulk("WORDMEANTRANS like '%{}%'".format(letters), letters, page)
    elif letters.find('*') != -1 or letters.find('?') != -1:
        lookUpInBulk("WORD like '{}'".format(letters.replace('*', '%').replace('?', '_')), letters, page)
    else:
        word = searchOneRecordFromDb("WORD = '{}'".format(letters.replace("'", "''")))
        if word!= None:
            showWordInfo(word)
        else:
            print("[SORRY] Word '{}' no exist in dictionary.".format(letters))
    closeDictDb()

def giveAWord():
    ''' Main enter of guessing word game '''
    global options
    openDictDb()
    isNewWord = False
    if (options.optForceNewWord or shouldLearnANewWord()) and not options.optForceReview:
        word = getANewWord()
        isNewWord = True
    else:
        word = getALearnedWord()
        if not word:
            word = getANewWord()
            isNewWord = True
    if not word:
        print('[ERROR] no more word available.')
        elegantExit()
    if isNewWord:
        showWordInfo(word)
    else:
        print('>> ', end = '')
        showWordMeaning(word)
    ans = ""
    correct = True
    score = 1
    times = 0
    killTheWord = False
    while ans != word[D_WORD]:
        ans = input('it\'s : ')
        if ans[0] == '!' and len(ans) > 1:
            ans = ans[1:]
            killTheWord = True
        if ans == '?':
            showWordInfo(word)
            correct = False
            score = 0
            break
        times += 1
    # if answer is correct, show the example sentence
    if correct and not isNewWord:
        showWordPhonetic(word)
        showWordSentence(word)
    # then conside retry > 3 as answer incorrect
    if times > 3:
        correct = False
        score = -1
    # Judge again
    if correct and killTheWord:
        killAWord(word)
    updateAWord(word, correct, score)
    closeDictDb()

def handle(signum, frame):
    ''' Handling Ctrl+C operation '''
    #os.system('clear')
    elegantExit()

# Main function
def main():
    global options
    signal.signal(signal.SIGINT, handle)
    parser = OptionParser(version="%prog v{}".format(APP_VERSION),
            usage="Usage: %prog [options] [word]\nTry '%prog --help' for more options")
    parser.set_defaults(optShowPicture = False, optPrintTranslation = False,
            optShowRawRecord = False, optForceNewWord = False, optForceReview = False,
            optPlayAudio = False, optRepeatTimes = 1)
    parser.add_option("-p", "--show-picture", dest="optShowPicture",
            action="store_true", help="show image of the word")
    parser.add_option("-a", "--play-audio", dest="optPlayAudio",
            action="store_true", help="play pronounce of the word")
    parser.add_option("-c", "--chinese", dest="optPrintTranslation",
            action="store_true", help="show Chinese translation")
    parser.add_option("-d", "--debug", dest="optShowRawRecord",
            action="store_true", help="dump database record for debug")
    parser.add_option("-n", "--force-new-word", dest="optForceNewWord",
            action="store_true", help="do not review a learned word")
    parser.add_option("-r", "--force-review", dest="optForceReview",
            action="store_true", help="always review a learned word")
    parser.add_option("-t", "--repeat-times", dest="optRepeatTimes",
            action="store", help="play giveaword n times")
    (opts, args) = parser.parse_args()
    options = opts
    if len(args) == 0:
        for time in list(range(int(options.optRepeatTimes))):
            giveAWord()
    elif len(args) == 1:
        lookUpAWord(args[0])
    elif len(args) == 2:
        lookUpAWord(args[0], args[1])
    else:
        print(parser.get_usage())

if __name__ == '__main__':
    main()

