#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Tue Jul 20 10:00:28 2021
@author: sabudoff

Current implentation on Ubuntu 20.04 uses 1.24 GB of RAM to run with an assets 
    folder containing 2.3 GB of data. All operations observed to use no more than 
    0.02 GB of RAM. No other programs were running except htop. 
'''

from PIL.Image import open as PIO
from PIL import ImageGrab
import glob, os, cv2, time, io
import numpy as np
import PySimpleGUI as sg
from tqdm import tqdm
# from sys import platform as PLATFORM


class VideoLoader():
    '''This class serves to read through the specified asset path in order to: 
        1) store all relevant movie frames in memory
        2) generate the frame that will display the movie, and
        3) house relevant methods for playing the movie'''
    def __init__(
                self,
                wd=os.getcwd(),
                assets='Assets',
                vidAssets='Stimuli',
                iconAssets='Icons'):

        # set asset paths
        self.wd=wd
        self.vid_path=os.path.join(wd, assets, vidAssets)
        self.icon_path=os.path.join(wd, assets, iconAssets)
        self.ico=os.path.join(self.icon_path, 'eye_icon.png')
        self.l1=PIO(os.path.join(self.icon_path, ('loading_eye_1.png')))
        self.l2=PIO(os.path.join(self.icon_path, ('loading_eye_2.png')))
        self.l3=PIO(os.path.join(self.icon_path, ('loading_eye_3.png')))

        # Make loading popup
        sg.theme('Black')
        self.loading=[
                        [sg.Text('Loading Video Files from ' + self.vid_path)],
                        [sg.Image(self.icon_path + '/loading_eye_1.png',
                                  key='-LOADIMAGE-')],
                        [sg.Button('', key='-INVISBUTTON-', visible=False)],
                        [sg.Text('Looking at what we got here',
                                 key='-LOADMESSAGE-')]
                        ]
        self.window=sg.Window('Visual Stimulus Lab Loader', self.loading,
                                element_justification='center',
                                keep_on_top=True, icon=self.ico,
                                finalize=True).Finalize()

        # Read in video files from the Stimuli Assets to make dicts
        self.videos, self.keyChain=self.VideoLoader()

        # Create buttons from dictionary
        self.levelClicked=4
        self.btns1=self.btnMaker(self.keyChain, level='btn1')
        self.btns2=self.btnMaker(self.keyChain, level='btn2', vis=False)
        self.btns3=self.btnMaker(self.keyChain, level='btn3', vis=False)
        self.clickedDictKeyPath=[None]

        self.movieLayout=[
                            #  Buttons for movie files
                            self.btns1,
                            self.btns2,
                            self.btns3,
                            # Current Frame of movie
                            [sg.Image(filename=os.path.join(self.icon_path,
                                      'Loading.png'), key='-MOVIE-')],
                            # Elements for controlling movie playback
                            [sg.pin(sg.Button(tooltip='Play', key='-PLAY-',
                                      disabled=True,
                                      image_filename=os.path.join(
                                      self.icon_path, 'play_eye.png'))),
                              sg.pin(sg.Button(tooltip='Stop', key='-STOP-',
                                      image_filename=os.path.join(self.icon_path,
                                      'stop_eye.png'), visible=False)),
                            # Element for tracking elapsed time
                              sg.Text('0000', key='-TIME_ELAPSED-'),
                            # This slide shows the playback positon of the movie
                              sg.Slider(range=(0, 1), enable_events=True,
                                    resolution=0.0001,
                                    disable_number_display=True,
                                    background_color='#83D8F5',
                                    orientation='h', disabled=True,
                                    key='-TIME-'),
                              # Elements for tracking total number of frames
                              sg.Text('0000', key='-TIME_TOTAL-'),
                              sg.pin(sg.Button(tooltip='Pause', key='-PAUSE-',
                                     image_filename=os.path.join(self.icon_path,
                                     'pause.png'), visible=False))]
                             ]
        # Close loading popup
        self.window.close()

##FUNCTIONS FOR LOADING VIDEO DATASETS#############################################################################
    def loadingScreen(self, image, message='Looking at what we got here'):
        ''' This method will update the loading screen'''
        image.thumbnail((400, 400))
        bio=io.BytesIO()
        image.save(bio, format='PNG')
        self.window['-LOADMESSAGE-'].update(message)
        self.window['-LOADIMAGE-'].update(data=bio.getvalue())
        self.window.Refresh()

    def framer(self, frames):
        '''This function will convert a list of .tif filepaths into a dict of arrays'''
        vidFrames={}
        self.loadingScreen(self.l1, message='Extracting frames')
        for i in range(len(frames)):
            im=PIO(frames[i])
            vidFrames[i]=np.array(im)
        self.loadingScreen(self.l2, message='Extracting frames')
        vidFrames['shape']=np.shape(np.array(im))
        vidFrames['N']=i
        return vidFrames
    
    def btnSmith(self, items,
                btnHandler='function',
                topLevel=None):
        '''This function will create a list of lists which can be used to generate buttons '''
        if type(items) == list:
            return [[item,  btnHandler, topLevel] for item in items]
        else:
            return [items, btnHandler, topLevel]
    
    def btnOrganizer(self, btnList):
        '''This function will appropriately group button lists'''
        # these two comprehensions find the unique elements in the function and group columns respectively
        funcs=list(set([btn[1] for btn in btnList]))
        groups=list(set([btn[2] for btn in btnList]))
        temp=[]
        self.loadingScreen(self.l3, message='Building buttons')
        for group in groups:
            self.loadingScreen(self.l1, message='Building buttons')
            for func in funcs:
               self.loadingScreen(self.l3, message='Building buttons')
               temp.append([btn for btn in btnList if btn[1] == func and btn[2]
 == group])
        return [i for i in temp if i !=[]]
                    
    def VideoLoader(self, handlers=['btn1', 'btn2', 'btn3']):
        ''' This Method will extract all of the videos in teh specified subdirectories
        wd is the working directory, be default it will be the directory in which this file is stored
        The output will be a dictionary containing each video as a frame by frame numpy array'''
        self.loadingScreen(self.l2, message='Looking at what we got here')
        videos={}
        keyChain=[]
        # Look for top level catagories; ie Naturalistic vs Labratory
        for dir1 in tqdm(sorted(glob.glob(os.path.join(self.vid_path, '*', ''))),
                         desc='Filling Top Level'):
            self.loadingScreen(self.l3)
            key=dir1[len(self.vid_path)+1:-1]
            vidCatagory={}
            # Look for subcatagories; ie Catcam, Mousecam, Cuttlefish
            for dir2 in tqdm(sorted(glob.glob(os.path.join(dir1, '*', ''))),
                             desc='Storing Videos'):
                self.loadingScreen(self.l2)
                key2=dir2[len(dir1):-1]
                vidName={}
                # If multiple dirs options are available in a given subcatagory, treat each as unique video
                subSubDirs=sorted(glob.glob(os.path.join(dir2, '*', '')))
                if len(subSubDirs) > 0:
                    for path in subSubDirs:
                        key3=path[len(dir2):-1]
                        
                        frames=sorted(glob.glob(os.path.join(path, '*.tif')))
                        if len(frames) > 0:
                            vidFrames=self.framer(frames)
                            vidName[key3]=vidFrames
                            keyChain.append(self.btnSmith(key3,
                                            btnHandler=handlers[2],
                                            topLevel=key2))
                # When no sub directories exist, extract all tifs 
                else:
                    self.loadingScreen(self.l3)
                    key3='Video'
                    frames=sorted(glob.glob(dir2 + '/*.tif'))
                    if len(frames) > 0:
                            vidFrames=self.framer(frames)
                            vidName[key3]=vidFrames
                vidCatagory[key2]=vidName
                videos[key]=vidCatagory
                keyChain.append(self.btnSmith(key2, btnHandler=handlers[1],
                                              topLevel=key))
            self.loadingScreen(self.l1)
            keyChain.append(self.btnSmith(key, btnHandler=handlers[0]))
        return videos, self.btnOrganizer(keyChain)
    
##FUNCTIONS FOR POPULATING PANEL BUTTONS#############################################################################                  
    def btnMaker(self, btnList, level, vis=True):
        '''Method for generating the simple GUI button widgets'''
        out=[]
        for i in range(len(btnList)):
            self.loadingScreen(self.l2, message='These are some nice looking buttons')
            temp=[]
            if btnList[i][0][1] == level:
                for j in range(len(btnList[i])):
                    item=btnList[i][j][0]
                    # The commented out line is appropriate when not grouping the elements in a frame, but rather on standard layout rows
                    temp.append(sg.pin(sg.Button(item, key=item, visible=vis)))
                    # temp.append(sg.Button(item, key=item, visible=vis))
            if temp !=[]:
                out.append(temp)
            self.loadingScreen(self.l3, message='These are some nice looking buttons')
        if len(out) == 1 and type(out[0]) == list:
            return out[0]
        else:
            return np.ravel(out).tolist()

    def buttonToggler(self, event, window):
        '''This Method determines the visibility of the buttons'''
        # Find the button level that was just clicked
        lastKeyClicked=self.clickedDictKeyPath[0]
        for ring in self.keyChain:
            for key in ring:
                if event == key[0]:
                    self.levelClicked=int(key[1][-1])
                    # Store dict keys for reaching bitmaps
                    self.clickedDictKeyPath=[key[2], key[0]]
        # Go through keys again, and turn off and on vis according to clicked
        for ring in self.keyChain:
            for key in ring:
                level=int(key[1][-1])
                # Modify visbility
                if (event == key[2] or
                    (level <=self.levelClicked and window[key[0]].visible)):
                    window[key[0]].Update(visible=True)
                    # Ensure toplevel key is maintained. This has only been tested to a depth of 3
                    if level < self.levelClicked - 1 and key[0] == lastKeyClicked:
                        self.clickedDictKeyPath.insert(0, key[0])
                else:
                    window[key[0]].Update(visible=False)
        if len(self.clickedDictKeyPath) < 3:
            self.clickedDictKeyPath.append('Video')
        # Note, the global availability of levelClicked and its continued counting is a hack to enable the webcam
        return self.clickedDictKeyPath[-3:], self.levelClicked + 1

##FUNCTIONS FORPLAYING THE MOVIE#####################################################################################
    def currentMovie(self):
        '''This Method crawls through the videos dict based on the selected keys'''
        temp=None
        for i in self.clickedDictKeyPath:
            try:
                if self.clickedDictKeyPath[0] == i:
                    temp=self.videos[i]
                else:
                    temp=temp[i]
            except:
                return None
        return temp

    def movieNight(self, event, window, currentMovie, frm_size, playing, onNow,
                   i, n_frames, control=True, external_control=False):
        '''THis function controls how the stimulus viewer functions including button actions, slider updating and encoding the image'''
        # This function in VideoLoader controls visibility of the buttons
        self.dictKeyPath, self.levelClicked=self.buttonToggler(event, window)

        try:
            n_frames=currentMovie['N']
        except:
            n_frames=0
        # Control scheme for the play/pause buttons and rendering the movie frames
        if currentMovie !=None and i <=n_frames:
            window['-PLAY-'].update(disabled=False)
            mov_frame=cv2.resize(currentMovie[i], frm_size)
            imgbytes=cv2.imencode('.png', mov_frame)[1].tobytes()
            window['-MOVIE-'].update(data=imgbytes)
        else:
            window['-PLAY-'].update(disabled=True)
            # print('Error rendering frame')
            i=0
            n_frames=0
        if event == '-PAUSE-' or event == '-STOP-' or onNow !=self.dictKeyPath:
            playing=False
            window['-PLAY-'].update(visible=True)
            window['-PAUSE-'].update(visible=False)
            window['-STOP-'].update(visible=False)
        if (event == '-PLAY-' or playing) and n_frames >=0:
            onNow=self.dictKeyPath
            playing=True
            window['-PLAY-'].update(visible=False)
            window['-PAUSE-'].update(visible=True)
            window['-STOP-'].update(visible=True)
            window['-TIME-'].update(value=i/(n_frames+0.0001))
            if not external_control:
                i +=1
        window['-TIME_ELAPSED-'].update('%04d' % (i,))
        window['-TIME_TOTAL-'].update('%04d' % (n_frames,))

        if not control:
            window['-PLAY-'].update(visible=False)
            window['-PAUSE-'].update(visible=False)
            window['-STOP-'].update(visible=False)

        # Determine the number of frames in the current video in order to loop the video
        if event == '-STOP-' or i > n_frames or onNow !=self.dictKeyPath:
            i=0
        return frm_size, playing, onNow, i, n_frames

    def smallScreen(self, window, currentMovie, i, frm_size=(200,200)):
        '''Generate the  small screen for the light path on the microscope'''
        mov_frame=cv2.resize(currentMovie[i], frm_size)
        imgbytes=cv2.imencode('.png', mov_frame)[1].tobytes()
        window['SMALLSCREEN'].update(data=imgbytes)
    def screenOFF(self, window, frm_size=(200,200)):
        '''When no movie is being shown to the small screen, hold the LCD off'''
        mov_frame=np.zeros((200,200))
        imgbytes=cv2.imencode('.png', mov_frame)[1].tobytes()
        window['SMALLSCREEN'].update(data=imgbytes)


class CameraLoader():

    def __init__(self, frm_size):
        self.dragging=False
        self.start_point=self.end_point=self.prior_rect=self.camera_ports=self.a_id=None
        self.ROI_time1=self.tPrevFrame=self.tNewFrame=self.timeStamp=self.graph_i=self.i_plot=self.prev_x=self.prevMean=self.newMean=0
        # Inits for the plot
        self.samples=300
        self.firstPlot=True
        self.figures=[]
        self.xPlotLim=500
        self.yPlotLim=255
        self.stats_log=[]
        self.roi_list=[['Full', (0,0), frm_size, None]]
        self.roi_stat_list = ['Full']

        self.camera_ports=self.list_ports()
        print('Camera Ports Available: ' + str(self.camera_ports.keys())[11:-2])

        # Buttons for making/manipulating ROIs
        roi_col=[[sg.T('Select left click action for\ncreating/manipulating ROIs',
                       enable_events=False)],
        [sg.R('Draw Rectangles', 1, key='-RECT-', enable_events=True)],
        [sg.R('Draw Circle', 1, key='-CIRCLE-', enable_events=True)],
        [sg.R('Move Item', 1, key='-MOVE-', enable_events=True)],
        [sg.R('Move Everything', 1, key='-MOVEALL-', enable_events=True)],
        [sg.R('Erase Item', 1, key='-ERASE-', enable_events=True)],
        [sg.B('Erase Everything', key='-CLEAR-')],
        [sg.Combo(self.roi_stat_list, default_value='Full', key='-ROICHOICE-',
                  tooltip='Select ROI to measure from')],
        [sg.Combo(['Mean', 'Median', 'Standard Deviation'],
                  default_value='Mean', key='-ROISTAT-',
                  tooltip='Select Statistic for ROI to display')],
        [sg.B('Save Image', key='-SAVESNAP-',
                  tooltip='Save a snapshot of the current view.\nIf no directory selected, one will be made on the desktop.')],
        [sg.B('Save Trace', key='-SAVETRACE-',
                  tooltip='Save the statistics log.\nIf no directory selected, one will be made on the desktop.')],
        ]

        cam_col=[self.cameraButtonMaker(),
                          [sg.Text('Digital Zoom'),
                # This slide shows the playback positon of the movie
                  sg.Slider(range=(1, 20), default_value=1, enable_events=True,
                            resolution=1, disable_number_display=True,
                            background_color='#83D8F5', orientation='h', key='-ZOOM-'),
                  # Elements for tracking total number of frames
                  sg.Text(' 1 X  ', key='-ZOOM_TOTAL-'),
                  sg.Checkbox('FPS Display', tooltip='Unchecking will remove the FPS tracker from the camera recordings',
                              default=True, key='-FPSBOOL-'),
                  sg.Checkbox('Time Stamp', tooltip='Unchecking will remove the Time Stamp from the camera recordings',
                              default=True, key='-TIMEBOOL-')],
                  [sg.Graph(frm_size,(0,frm_size[1]), (frm_size[0],0), key='-CAM-',
                            enable_events=True, drag_submits=True,
                            right_click_menu=[[],['-Erase ROI-',]]
                    )],
                  [sg.Graph((frm_size[0], 122), (0, 0), (self.xPlotLim,
                            self.yPlotLim),background_color='black', key='-GRAPH-')]
                    ]
        self.camLayout=[[sg.Col(cam_col, key='-cam_COL-'), sg.Col(roi_col,
                            key='-roi_COL-') ]]

    def list_ports(self, n_cams=5):
        '''
        Test the ports and returns a tuple with the available ports and the ones that are working.
        Inspired by G M 2020-06-29 https://stackoverflow.com/questions/57577445/list-available-cameras-opencv-python
        '''
        working_ports={}
        i=0
        for port in range(n_cams):
            camera=cv2.VideoCapture(port)
            if camera.isOpened():
                is_reading, img=camera.read()
                shape=(camera.get(3), camera.get(4))
                if is_reading:
                    # print('Port %s is working and reads images %s' %(port,shape))
                    working_ports['Port ' + str(i)]={'ID' : port, 'Shape' : shape}
                    i +=1
            camera.release()
        camera.release()
        return working_ports

    def cameraButtonMaker(self, real=True):
        '''This function makes the button row for calling cameras '''
        out=[]
        if real:
            for i in range(len(self.camera_ports)):
                current=self.camera_ports['Port ' + str(i)]
                out.append(sg.pin(sg.Button('Port ' + str(current['ID']),
                                            key='*CAM' + str(i))))
        else:
            out.append(sg.pin(sg.Button('Port 1', key='*CAM1')))
        return out

    def lca(self, event, cap=None):
        '''This function allows changing the camera on the fly. Lights Cameras Action!'''
        if cap !=None or type(event) !=str:
            return cap
        if event[:-1] == '*CAM':
            if cap !=None:
                cap.release()
            port=self.camera_ports['Port ' + event[-1]]['ID']
            print(self.camera_ports['Port ' + event[-1]]['ID'])
            return cv2.VideoCapture(port)
        if event == 'Action!':
            port=self.camera_ports['Port 0']['ID']
            print('Starting with Port ' + str(port))
            return cv2.VideoCapture(port)

    def cameraDisplay(self, cam_frame, event, values, window, frm_size,
                      zoomEnabled=True):
        '''This method will update and display the current frame for the display'''
        # print(self.roi_list)
         # Check user interaction with the ROI
        if event == '-CLEAR-':
            window['-CAM-'].erase()
            self.roi_list=[['Full', (0,0), frm_size, None]]
        if event == '-CAM-':
            self.ROIcontroller(window, event, values)
        # Read User desired Zoom and adjust image accordingly
        # self.newMean=np.mean(cam_frame[:,:,1])

        if zoomEnabled:
            zoom=values['-ZOOM-']
            # This hack is because something is wrong with my zoom cropping math
            if zoom == 3 or zoom == 2:
                zoom=4
            window['-ZOOM_TOTAL-'].update(' %d X' % zoom)
            cam_frame=self.enhanceEnhance(cam_frame, zoom)
            # Resize Frame for timestamp
            cam_frame=cv2.resize(cam_frame, frm_size)
        # Calculate and display FPS and timestamp if desired
        self.tNewFrame=time.time()
        fps='FPS = ' + str(int(1/(self.tNewFrame-self.tPrevFrame)))
        self.timeStamp=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
        self.tPrevFrame=self.tNewFrame
        if values['-FPSBOOL-']:
            cv2.putText(cam_frame, fps, (7, 40), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        1, (0, 0, 255), 2, cv2.LINE_AA)
        if values['-TIMEBOOL-']:
            cv2.putText(cam_frame, self.timeStamp, (7, 20), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                        1, (0, 0, 255), 2, cv2.LINE_AA)
        # Encode and display cam feed

        self.trimROI(cam_frame)

        cam_imgbytes=cv2.imencode('.png', cam_frame)[1].tobytes()
        # window['-CAM-'].update(data=cam_imgbytes)
        if self.a_id:
            window['-CAM-'].delete_figure(self.a_id)             # delete previous image
        self.a_id=window['-CAM-'].draw_image(data=cam_imgbytes, location=(0,0))    # draw new image
        window['-CAM-'].send_figure_to_back(self.a_id)            # move image to the 'bottom' of all other drawings


    def enhanceEnhance(self, cam_frame, zoom):
        '' 'This method appropriately crops frames prior to zooming in via interpolation'''
        x0=self.camera_ports['Port 0']['Shape'][1]
        y0=self.camera_ports['Port 0']['Shape'][0]
        scale=1/zoom
        x1=(x0/2) - (2*scale*x0)
        x2=(x0/2) + (2*scale*x0)
        y1=(y0/2) - (2*scale*y0)
        y2=(y0/2) + (2*scale*y0)
        temp=cam_frame[int(x1):int(x2), int(y1):int(y2), :]
        cam_frame=cv2.resize(temp, None, fx=zoom, fy=zoom,
                               interpolation=cv2.INTER_LINEAR)
        return cam_frame

    def ROIcontroller(self, window, event, values):
        '''Modified version of the PySimpleGUI demo project Graph Drawing and Dragging 
        https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drawing_And_Dragging_Figures.py '''
        if event in ('-MOVE-', '-MOVEALL-'):
            window['-CAM-'].set_cursor(cursor='fleur')          # not yet released method... coming soon!
        elif not event.startswith('-CAM-'):
            window['-CAM-'].set_cursor(cursor='left_ptr')       # not yet released method... coming soon!
        if event == '-CAM-':  # if there's a 'Graph' event, then it's a mouse
            x, y=values['-CAM-']
            ROI_time0=self.tNewFrame
            delta_ROI_time=ROI_time0 - self.ROI_time1
            self.ROI_time1=ROI_time0
            if delta_ROI_time > 0.2:
                self.start_point, self.end_point=None, None  # enable grabbing a new rect
                self.dragging=False
                self.prior_rect=None
            if not self.dragging:
                self.start_point=(x, y)
                self.dragging=True
                self.drag_figures=window['-CAM-'].get_figures_at_location((x,y))
                self.lastxy=x, y
            else:
                self.end_point=(x, y)
            if self.prior_rect:
                window['-CAM-'].delete_figure(self.prior_rect)
            self.delta_x, self.delta_y=x - self.lastxy[0], y - self.lastxy[1]
            self.lastxy=x,y
            if None not in (self.start_point, self.end_point):
                # print(values['-ERASE-'])
                if values['-MOVE-']:
                    for fig in self.drag_figures:
                        window['-CAM-'].move_figure(fig, self.delta_x, self.delta_y)
                        window['-CAM-'].update()
                elif values['-RECT-']:
                    self.prior_rect=window['-CAM-'].draw_rectangle(self.start_point,
                                    self.end_point,fill_color=None, line_color='red',
                                    line_width=3)
                    self.roi_list.append(['Rect', self.start_point,
                                          self.end_point, self.drag_figures])
                elif values['-CIRCLE-']:
                    self.prior_rect=window['-CAM-'].draw_circle(self.start_point,
                                    self.end_point[0]-self.start_point[0],
                                    fill_color=None, line_color='red',
                                    line_width=3)
                    self.roi_list.append(['Circ', self.start_point,
                                          self.end_point, self.drag_figures])
                elif values['-ERASE-']:
                    for figure in self.drag_figures:
#!!! I am unable to figure out a way to identify the fiure I am deleting in order to remove it from the roi_list
                        try:
                            print(window['-CAM-'].get_figures_at_location(self.drag_figures))
                            print(window['-CAM-'].get_bounding_box(self.drag_figures))
                        except:
                            pass
                        # print(figure)
                        # print(self.drag_figures)
                        print(self.roi_list)
                        window['-CAM-'].delete_figure(figure)
                        window['-CAM-'].update()
                        # self.roi_list=self.roi_list[self.roi_list[:][3]!=figure]
                        print(self.roi_list)
                elif values['-MOVEALL-']:
                    window['-CAM-'].move(self.delta_x, self.delta_y)

        # Trim the ROI List to not include the inner drage events
        if len(self.roi_list) > 2 and self.roi_list[-2][1] == self.roi_list[-1][1]:
            self.roi_list.remove(self.roi_list[-2])


        # !!! This is why the ROIs are not being generated properly, for some reason I am preventing PySimpleGUI from detecting mouse up events
        # I have hacked this with my deltaROI timing but it is a jankier solution and I think blocks the right click erasure
        # elif event.endswith('+UP'):  # The drawing has ended because mouse up
            # self.start_point, self.end_point=None, None  # enable grabbing a new rect
            # self.dragging=False
            # self.prior_rect=None
        # elif event == '-Erase ROI-':
        #     if values['-CAM-'] !=(None, None):
        #         self.drag_figures=window['-CAM-'].get_figures_at_location(values['-CAM-'])
        #         for figure in self.drag_figures:
        #             window['-CAM-'].delete_figure(figure)

    def graphGenerator(self, window, values):
        self.roiChooser(window,values)
        if len(self.stats_log)>2:
            if values['-ROISTAT-'] == 'Mean':
                stat=2
            elif values['-ROISTAT-'] == 'Median':
                stat=4
            if values['-ROISTAT-'] == 'Standard Deviation':
                stat=3

            current = [self.stats_log[i] for i in range(len(self.stats_log))
                       if self.stats_log[i][1] == values['-ROICHOICE-']]

            if len(current) > 2:
                self.new_y=current[-1][stat]
                self.prev_y=current[-2][stat]
                self.plotROI(window)

    def plotROI(self, window):
        # Create X and Y axis
        if self.firstPlot:
            self.STEP_SIZE=1
            window['-GRAPH-'].draw_line((10, 0), (10,self.yPlotLim),color='white')
            window['-GRAPH-'].draw_line((0,10), (self.xPlotLim, 10),color='white')
            self.firstPlot=False
        # This allows the window['-GRAPH-'] to move forward
        self.new_x=self.i_plot
        if self.i_plot >=self.xPlotLim:
            window['-GRAPH-'].delete_figure(self.figures[0])
            self.figures=self.figures[1:]
            for count, figure in enumerate(self.figures):
                window['-GRAPH-'].move_figure(figure, -self.STEP_SIZE, 0)
            self.prev_x=self.prev_x - self.STEP_SIZE

        last_figure=window['-GRAPH-'].draw_line((self.prev_x, self.prev_y),
                                    (self.new_x, self.new_y), color='white')
        self.figures.append(last_figure)
        # self.prev_x, self.prev_y=self.new_x, self.new_y
        self.prev_x=self.new_x
        self.i_plot +=self.STEP_SIZE if self.i_plot < self.xPlotLim else 0

    def roiChooser(self, window, values):
        '''This method updates the ROI choice combo box with the present options '''
        # ID all rois and store as a list
        temp = []
        for i in range(len(self.roi_list)):
           name = self.roi_list[i][0]
           if name != 'Full':
               name = name + ' ' + str(i)
           temp.append(name)
        # Ensure the approprate ROI is chosen each iteration of the event loop
        last_roi_choice = values['-ROICHOICE-']
        if last_roi_choice not in temp:
            last_roi_choice = 'Full'
        window.Element('-ROICHOICE-').Update(value = last_roi_choice, values = temp)

    def trimROI(self, cam_frame):
        '''This helper method feeds the current roi list into the stats_log'''
        for i in range(len(self.roi_list)):
            if self.roi_list[i][0] == 'Full':
                self.dataLogger(cam_frame, 'Full')
            elif self.roi_list[i][0] == 'Rect':
                self.dataLogger(cam_frame, 'Rect ' + str(i), i=i)
            elif self.roi_list[i][0] == 'Circ':
                self.dataLogger(cam_frame, 'Circ ' + str(i), i=i)

    def dataLogger(self, cam_frame, name, channel=1, i=0):
        '''This method will calculate and store ROI data'''
        if name == 'Full':
            if channel=='all':
                region=cam_frame[:,:,:]
            else:
                region=cam_frame[:,:,channel]
        elif name[0:4] == 'Rect':
            start, stop=self.roi_list[i][1], self.roi_list[i][2]
            y1, y2 = min(start[1], stop[1]), max(start[1], stop[1])
            x1, x2 = min(start[0], stop[0]), max(start[0], stop[0])
            if channel=='all':
                region=cam_frame[y1:y2,  x1:x2, :]
            else:
                region=cam_frame[y1:y2,  x1:x2, channel]
        elif name[0:4] == 'Circ':
            center, stop=self.roi_list[i][1], self.roi_list[i][2]
            radius=int(np.sqrt((center[0] - stop[0])**2 + (center[1] - stop[1])**2))
            region=self.circle_crop(cam_frame, center, radius, channel)
        else:
            return
        mean=np.mean(region)
        std=np.std(region)
        median=np.median(region)
        self.stats_log.append([self.tNewFrame, name, mean, std, median])

    def circle_crop(self, img, center, radius, channel):
        ''' Function for cropping a circular region, courtesy of nathancy https://stackoverflow.com/questions/60118622/how-to-crop-circle-image-from-webcam-opencv-and-remove-background'''
        if channel == 0:
            channel = (255,0,0)
        elif channel == 1:
            channel = (0,255,0)
        elif channel == 2:
            channel = (0,0,255)
        elif channel == 'all':
            channel = (255,255,255)
        circle_mask = np.zeros(img.shape, dtype=np.uint8)
        cv2.circle(circle_mask, center, radius, channel, -1)
        # Bitwise-and for ROI
        ROI=cv2.bitwise_and(img, circle_mask)
        # Crop mask and turn background white
        circle_mask=cv2.cvtColor(circle_mask, cv2.COLOR_BGR2GRAY)
        x,y,w,h=cv2.boundingRect(circle_mask)
        result=ROI[y:y+h,x:x+w]
        circle_mask=circle_mask[y:y+h,x:x+w]
        result[circle_mask == 0]=(255,255,255)
        return result

    def folderFinder(self, values, onNow, snap=False, trace=False):
        '''This function will create the necessary save path'''
        root=values['-SAVEDIR-']
        if not os.path.isdir(root):
            root=os.path.expanduser('~/Desktop')
        dir_name='VSL_Experiment_'
        try:
            dir_name=dir_name + self.timeStamp[:10]
        except:
            pass
        dir_path=os.path.join(root, dir_name)
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
            print('Directory created: ' + dir_path)
        else:
            print('Directory exists: ' + dir_path)
        os.chdir(dir_path)
        name=values['-EXPNOTE-']
        stim_param=onNow[0] + '_' + onNow[1] + '_' + onNow[2]
        if values['-STIMSTAMP-']:
            name=name + stim_param
        if values['-DATESTAMP-']:
            name=name + '_' + self.timeStamp[:10] + '_' + self.timeStamp[12:]
        if snap:
            name=name + '_snapshot'
        elif trace:
            name=name + '_trace'
        print('saving to: ' + name)
        file=os.path.join(dir_path, name)
        return file, stim_param

#!!! Thos function is currently borken and thus left disabled
    def quickSave(self, window, event, values, onNow):
        '''This function controls the saving feature of the quick save buttons. The code for the graph save including widgets is adapted from of https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drawing_And_Dragging_Figures.py '''
        if event == '-SAVESNAP-':
            print('snap')
            file, stim_param=self.folderFinder(values, onNow, snap=True)
            file=file + '.png'
            widget=window['-CAM-'].Widget
            box=(widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_rootx()
                   + widget.winfo_width(), widget.winfo_rooty() + widget.winfo_height())
            grab=ImageGrab.grab(bbox=box)
            grab.save(file)
        if event == '-SAVETRACE-':
            print('tace')
            file, stim_param=self.folderFinder(values, onNow, snap=True)
            F=open(file + '.txt', 'a')
            F.writelines(self.stats_log)
            F.close()

    # def roiCutter(self, )

def main(frm_size=(650,500)):

    def TTL(state):
        '''This function will be updated if hardware pre and post the recording is desired '''
        print('TTL ' + state)

    def experimentRunner(values, onNow, n_frames, playing,
              cam_frame, event, window, frm_size):
        '''This function controls the recording of an experiment. It will populate a directory with timestamped png files and a log of when each frame was aquired relative to the video frame displayed '''
        window['-STARTEXP-'].Update(disabled=True)
        window['-CANCEL-'].Update(disabled=False)
        window['-RECORDBOOL-'].update(disabled=True)
        window['-RECT-'].update(disabled=True)
        window['-CIRCLE-'].update(disabled=True)
        window['-ERASE-'].update(disabled=True)
        window['-CLEAR-'].update(disabled=True)
        window['-MOVEALL-'].update(disabled=True)
        window['-MOVE-'].update(disabled=True)
        window['-SAVESNAP-'].update(disabled=True)
        window['-SAVETRACE-'].update(disabled=True)
        # window['-CAM-'].update(disabled=True)

        # This hack ensures the experiment starts if no video yet played
        i=0
        event='-PLAY-'
        playing=True
        frm_size, playing, onNow, i, n_frames=v.movieNight(event, window,
            currentMovie, frm_size, playing, onNow, i, n_frames, control=False)
        if onNow == None:
            return
        # The below will ensure a directory is prepared to recieve experiment
        if values['-RECORDBOOL-']:
            file, stim_param=c.folderFinder(values, onNow)
        
            # Prior to the experiment, a text file will be initialized and
                #a ttl pulse will be sent to relevant external hardware
            F=open(file + '.txt', 'a')
        TTL('ON')
        # prevMean=0
        # Experimental loop
        for i in range(n_frames):
            event, values=window.read(timeout=11)
            if values['-RECORDBOOL-']:
                file_i=file + '_%04d' %i + '.png'
            # If playback for the experimenter is not desired it will not be rendered
            if values['-PLAYWITHEXP-']:
                frm_size, playing, onNow, i, n_frames=v.movieNight(event,
                    window, currentMovie, frm_size, playing, onNow, i, n_frames,
                    control=False, external_control=True)
            # Run Small Screen for stage light path
            v.smallScreen(stageWindow, currentMovie, i)
            # The camera recording occurs here
            ret, cam_frame=cap.read()
            c.cameraDisplay(cam_frame, event, values, window, frm_size,
                            zoomEnabled=False)
            if values['-RECORDBOOL-']:
                cv2.imwrite(file_i, cam_frame)
                # Experimental log for the current iteration is recorded
                F.writelines('%s : %s : %s \n' %(file_i, stim_param, c.tNewFrame))
    
            # Experimenter can cancel the recording if necessary
            if event == '-CANCEL-':
                break
        # Following recording the log is finalized and the TTL associted device is disabled
        v.screenOFF(stageWindow)
        TTL('OFF')
        if values['-RECORDBOOL-']:
            F.close()
        playing=False
        window['-CANCEL-'].Update(disabled=True)
        window['-PLAY-'].update(visible=True)
        window['-RECORDBOOL-'].update(disabled=False)
        window['-RECT-'].update(disabled=False)
        window['-CIRCLE-'].update(disabled=False)
        window['-ERASE-'].update(disabled=False)
        window['-CLEAR-'].update(disabled=False)
        window['-MOVEALL-'].update(disabled=False)
        window['-MOVE-'].update(disabled=False)
        window['-SAVESNAP-'].update(disabled=False)
        window['-SAVETRACE-'].update(disabled=False)
        # window['-CAM-'].update(disabled=False)
        return playing

    # Initialize global vars
    playing=False
    onNow=None
    n_frames=0
    i=0
    # prevMean=0
    # Read in the video assets
    v=VideoLoader()
    # Initialize the camera assets
    c=CameraLoader(frm_size)
    # Create the GUI
    layout=[[sg.Text("To record an experiment, first select a Stimulus Movie from the detected options in the left hand frame, the desired camera from the options detected on the right and finally the directory to save recordings to in the bottom browser.\nTo stimulate without recording simply select the desired stimulus and unselect the \"Record Experiment\" checkbox. \nNow, let's see some science!\n"
                       , justification='center')],
                [sg.Frame('Stimulus Movie', v.movieLayout),
                 sg.Frame('Video Stream', c.camLayout)],
                [sg.Text('Save Location', tooltip='A folder with todays date will be created in this directory',
                         size=(15, 1), auto_size_text=False, justification='right'),
                 sg.InputText('', key='-SAVEDIR-'), sg.FolderBrowse()],
                [sg.Text('Experiment Note', size=(15, 1), auto_size_text=False,
                         justification='right'), sg.InputText('', key='-EXPNOTE-'),
                 sg.Checkbox('Stimulus', key='-STIMSTAMP-', tooltip='Checking will include stimulus name in file name',
                             default=True),
                 sg.Checkbox('Date Stamp', key='-DATESTAMP-', tooltip='Checking will include date stamp in file name',
                             default=True),
                 sg.Checkbox('Display Stim During Recording', key='-PLAYWITHEXP-',
                             tooltip='Checking will play the movie on both screens',
                             default=True),
                 sg.Checkbox('Record Experiment', key='-RECORDBOOL-',
                             tooltip='WARNING: Unchecking will prevent data aquisition',
                             default=True)],
                [sg.Submit(button_text='Begin Experiment', key='-STARTEXP-',
                           tooltip='Click to submit this window',
                           disabled=True), sg.Cancel(key='-CANCEL-', disabled=True)]]
    sg.theme('Black')
    window=sg.Window('Visual Stimulus Lab', layout, keep_on_top=True,
                       return_keyboard_events=True,
                       element_justification='center', icon=v.ico,
                       resizable=False).Finalize()
    window.Maximize()
    # Create Small Screen
    stageWindow=sg.Window('', layout=[[sg.Image('', key='SMALLSCREEN',
                            s=(200,200))]], location=(0,0), icon=v.ico,
                            force_toplevel=True, no_titlebar=True, keep_on_top=True,
                            element_justification='center').Finalize()
    # Initialize the camera
    cap=cv2.VideoCapture(-1)
    time.sleep(0.5)
    ret, cam_frame=cap.read()
    # Main event loop
    while True:
        # Run GUI window
            # 11 is the shortest timeout that works on my computer.
            # The lower it is the faster the frame rate since read affectively pauses the event loop for up to timeout
        event, values=window.read(timeout=11)
        # Detect loss of window and end the event loop
        if event == sg.WIN_CLOSED:
            break

        # Run Camera, with desired port
        cap=c.lca(event, cap=cap)

        # try:
        ret, cam_frame=cap.read()
            # print(cam_frame)
        if type(cam_frame) !=type(None):
            c.cameraDisplay(cam_frame, event, values, window, frm_size,
                        zoomEnabled=True)
        # except:
        #     print('error')
        elif not ret:
            print('Camera Disconnected')
        c.graphGenerator(window, values)
        if onNow:
            # CUrrently, both quick saves have minor bugs and their event is disabled
            window['-SAVESNAP-'].update(disabled=False)
            window['-SAVETRACE-'].update(disabled=False)
            # c.quickSave(window, event, values, onNow)
        else:
            window['-SAVESNAP-'].update(disabled=True)
            window['-SAVETRACE-'].update(disabled=True)

        # Find the movie to load into the Movie display
        currentMovie=v.currentMovie()
        # Control scheme for the movie playback
        frm_size, playing, onNow, i, n_frames=v.movieNight(event, window,
                        currentMovie, frm_size, playing, onNow, i, n_frames)

        if currentMovie !=None:
            if isinstance(currentMovie[0], np.ndarray) and (os.path.isdir(values['-SAVEDIR-'])
                                                    or not values['-RECORDBOOL-']):
                window['-STARTEXP-'].Update(disabled=False)
                if event == '-STARTEXP-':
                    playing=experimentRunner(values, onNow, n_frames, playing,
                      cam_frame, event, window, frm_size)
            else:
                window['-STARTEXP-'].Update(disabled=True)
        else:
            window['-STARTEXP-'].Update(disabled=True)

    # Shut down all assets
    cv2.destroyAllWindows()
    window.close()
    stageWindow.close()
    cap.release()


if __name__ == '__main__':
    main()