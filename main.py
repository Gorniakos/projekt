#!/usr/bin/env python
#-*- coding: latin-1 -*-
import csv
import yaml
import random
import atexit
import codecs

from typing import List, Dict, Tuple
from os.path import join
from psychopy import visual, event, logging, gui, core


@atexit.register
def save_beh_results() -> None:
    file_name = PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'
    with open(join('results', file_name), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def show_image(win: visual.window, file_name: str, size: List[int], key: str = 'f7') -> None:
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=[key, 'return', 'space'])
    if clicked == [key]:
        logging.critical('Experiment finished by user! {} pressed.'.format(key[0]))
        exit(0)
    win.flip()


def read_text_from_file(file_name: str, insert: str = '') -> str:
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key: str = 'f7') -> None:
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win: visual.Window, file_name: str, insert: str = '') -> None:
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth= 900)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err: str) -> None:
    logging.critical(err)
    raise Exception(err)


# GLOBALS

RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Block number', 'Trial number', 'Button pressed', 'Reaction time', 'Stim word', 'Trial type', 'Experimental'])  # ... Results header


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info: Dict = {'ID': '', 'Sex': ['M', "F"], 'Age': ''}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Experiment title, fill by your name!')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')

    clock = core.Clock()
    # load config, all params should be there
    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)
    frame_rate: int = conf['FRAME_RATE']
    screen_res: List[int] = conf['SCREEN_RES']
    # === Scene init ===
    win = visual.Window(screen_res, fullscr=False, monitor='testMonitor', units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    #fix = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])

    PART_ID = info['ID'] + info['Sex'] + info['Age']
    logging.LogFile(join('results', f'{PART_ID}.log'), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(screen_res))

    # === Prepare stimulus here ===
    stim = visual.TextStim(win, text=random.choice(random.choice(conf['STIM_WORD'])), height=conf['STIM_SIZE'], color=random.choice(conf['STIM_COLOR']))
    question_frame = visual.TextStim(win, text='odpowiedz', height=conf['STIM_SIZE'], color='black')

    # === Training ===
    show_info(win, join('.', 'messages', 'Instruction_1.txt'))
    show_info(win, join('.', 'messages', 'Instruction_2.txt'))
    show_info(win, join('.', 'messages', 'Instruction_3.txt'))
    show_info(win, join('.', 'messages', 'before_training.txt'))
    csi_list = [conf['TRAINING_CSI']] * conf['NO_TRAINING_TRIALS'][1]

    for trial_no, csi in enumerate(csi_list, 1):
        key_pressed, rt = run_trial(win, conf, clock) # stim_word, trial_type
        corr = 1 if key_pressed == 'z' else 0,
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock.getTime())  # , timeStamped=clock
        rt = clock.getTime()
        #return(stim)
        #stim_word = stim
        if reaction:  # break if any button was pressed
            break
        RESULTS.append([PART_ID, 'training', trial_no, key_pressed, rt])# rt, stim_word, trial_type, 'training'])

        # it's a good idea to show feedback during training trials
        feedb = "Poprawnie" if corr else "Niepoprawnie"
        feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])
        feedb.draw()
        win.flip()
        core.wait(1)
        win.flip()

    # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))

    for block_no in range(conf['NO_BLOCKS']):
        for _ in range(conf['TRIALS_IN_BLOCK']):
            key_pressed, rt = run_trial(win, conf, clock) #stim_word
            RESULTS.append([PART_ID, block_no, trial_no, key_pressed, rt])
            trial_no += 1
#        show_image(win, join('.', 'images', 'break.jpg'), size=screen_res)

    # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()

def run_trial(win, conf, clock):
    
    # === Start pre-trial  stuff (Fixation cross etc.)===
    fix = visual.TextStim(win, text='+', height=50, color=conf['FIX_CROSS_COLOR'])
    stim = visual.TextStim(win, text=random.choice(conf['STIM_WORD']), height=conf['STIM_SIZE'], color=random.choice(conf['STIM_COLOR']))

    for _ in range(conf['FIX_CROSS_TIME']):
        fix.draw()
        win.flip()
        core.wait(1)
    stim.draw()
    event.clearEvents()
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):  # present stimuli
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS'])) #, timeStamped=clock
        rt = clock.getTime()
#        return(stim)
#        stim_word = stim
        if reaction:  # break if any button was pressed
            break
        stim.draw()
        win.flip()

    #if not reaction:  # no reaction during stim time, allow to answer after that
        #question_frame.draw()
        #question_label.draw()
        #win.flip()
        #reaction = event.waitKeys(keyList=list(conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME'], timeStamped=clock)
    # === Trial ended, prepare data for send  ===
    if reaction:
        key_pressed = reaction[0]
        rt = rt
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0

    return key_pressed, rt  # return all data collected during trial

if __name__ == '__main__':
    PART_ID = ''
    main()