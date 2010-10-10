import sys
import os
import xbmc
import xbmcgui
from utilities import *
import urllib
import unzip
import unicodedata
import shutil
import socket

_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__settings__ = sys.modules[ "__main__" ].__settings__

STATUS_LABEL = 100
LOADING_IMAGE = 110
SUBTITLES_LIST = 120
SERVICE_DIR = os.path.join(os.getcwd(), "resources", "lib", "services")

EXIT_SCRIPT = ( 9, 10, 247, 275, 61467, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )

class GUI( xbmcgui.WindowXMLDialog ):
        
    def __init__( self, *args, **kwargs ):
        
        pass
          

    def set_allparam(self):
        
        temp = False
        rar = False
        movieFullPath = urllib.unquote(xbmc.Player().getPlayingFile())
        path = __settings__.getSetting( "subfolder" ) == "true"      # True for movie folder
        sub_folder = xbmc.translatePath(__settings__.getSetting( "subfolderpath" ))
        
        if (movieFullPath.find("http://") > -1 ):
            temp = True

        if (movieFullPath.find("rar://") > -1 ) and path:
            rar = True
            
            movieFullPath = sub_folder = movieFullPath.replace("rar://","")
            sub_folder = os.path.dirname(os.path.dirname( sub_folder ))
                
        if not path and not rar:
            if len(sub_folder) < 1 :
                sub_folder = os.path.dirname( movieFullPath )
                              
        if path and not rar:
            if sub_folder.find("smb://") > -1:
                if temp:
                    dialog = xbmcgui.Dialog()
                    sub_folder = dialog.browse( 0, "Choose Subtitle folder", "files")
                else:
                    sub_folder = os.path.dirname( movieFullPath )
            else:
                sub_folder = os.path.dirname( movieFullPath )   

        
        
        self.list = []
        
        self.year      = xbmc.getInfoLabel("VideoPlayer.Year")        # Year
        self.season    = str(xbmc.getInfoLabel("VideoPlayer.Season")) # Season
        self.episode   = str(xbmc.getInfoLabel("VideoPlayer.Episode"))# Episode        
        if self.episode.lower().find("s") > -1:                       # Check if season is "Special"             
            self.season = "0"                                         #
            self.episode = self.episode[-1:]                          #
        
        self.tvshow    = xbmc.getInfoLabel("VideoPlayer.TVshowtitle") # Show
        self.title     = unicodedata.normalize('NFKD', 
                         unicode(unicode(xbmc.getInfoLabel
                         ("VideoPlayer.Title"), 'utf-8'))
                         ).encode('ascii','ignore')                   # Title
        
        if self.tvshow == "":
            if str(self.year) == "":
                title, season, episode = regex_tvshow(False, self.title)
                if episode != "":
                    self.season = str(int(season))
                    self.episode = str(int(episode))
                    self.tvshow = title
                else:
                    self.title, self.year = xbmc.getCleanMovieTitle( self.title )
 
            else:
                self.title = self.title  
        else:
            self.year = ""
        self.language_1 = __settings__.getSetting( "Lang1" )                    # Full language 1
        self.language_2 = __settings__.getSetting( "Lang2" )                    # Full language 2  
        self.language_3 = __settings__.getSetting( "Lang3" )                    # Full language 3
       
        label_colour = __settings__.getSetting( "label_colour" )                # Service Label Colour 
        if label_colour == "Blue":
          self.label_colour = "0084ff"
        elif label_colour == "White":
          self.label_colour = "FFFFFF"          
        elif label_colour == "Red":
          self.label_colour = "FF0000"
        elif label_colour == "Green":
          self.label_colour = "097054"
        elif label_colour == "Yellow":
          self.label_colour = "FFDE00"
        elif label_colour == "Orange":
          self.label_colour = "FF9900"
        elif label_colour == "Grey":
          self.label_colour = "777B88"          
                                       
        self.sub_folder = sub_folder                                            # Subtitle download folder

        self.file_original_path = urllib.unquote ( movieFullPath )              # Movie Path
        
        self.set_temp = temp
        
        if __settings__.getSetting( "disable_hash_search" ) == "true":
           self.set_temp = True

        self.mansearch =  __settings__.getSetting( "searchstr" ) == "true"      # Manual search string??
        self.parsearch =  __settings__.getSetting( "par_folder" ) == "true"     # Parent folder as search string
        self.rar = rar                                                          # rar archive?

        if (__settings__.getSetting( "fil_name" ) == "true"):                   # Display Movie name or search string
          self.file_name = os.path.basename( movieFullPath )
        else:
          if (len(str(self.year)) < 1 ) :
            self.file_name = self.title
            if (len(self.tvshow) > 0):
              self.file_name = "%s S%.2dE%.2d" % (self.tvshow, int(self.season), int(self.episode) )
          else:
            self.file_name = "%s (%s)" % (self.title, str(self.year),)    
          
          
        self.tmp_sub_dir = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( os.getcwd() ),"sub_tmp" )
        
        
        if not self.tmp_sub_dir.endswith(':') and not os.path.exists(self.tmp_sub_dir):
          os.mkdir(self.tmp_sub_dir)
        else:
          self.rem_files(self.tmp_sub_dir)
        
        self.getControl( 111 ).setVisible( False ) # check for existing subtitles and set to "True" if found
        sub_exts = ["srt", "sub", "txt", "smi", "ssa", "ass" ]
        br = 0
        for i in range(3):
          for sub_ext in sub_exts:
            if br == 0:
              exec("lang = toOpenSubtitles_two(self.language_%s)" % (str(i+1)) )
              if os.path.isfile ("%s.%s.%s" % (os.path.join(sub_folder,os.path.splitext( os.path.basename( self.file_original_path ) )[0]),lang ,sub_ext,)):
                self.getControl( 111 ).setVisible( True )
                br = 1
                break
#### ---------------------------- Set Service ----------------------------###     

        def_service = __settings__.getSetting( "defservice")
        def_movie_service = __settings__.getSetting( "defmovieservice")
        def_tv_service = __settings__.getSetting( "deftvservice")
        service_list = []
        standard_service_list  = ['Titulky','OpenSubtitles', 'Podnapisi', 'Sublight', 'Bierdopje', 'Subscene', 'Ondertitel', 'Undertexter', 'Napiprojekt', 'Titlovi', 'LegendasTV']
        service = ""
 
        for name in os.listdir(SERVICE_DIR):
           if not (name.startswith('.')) and not (name.startswith('_')):
              service_list.append(name)

        for serv in standard_service_list:
          if not __settings__.getSetting( serv ) == "true" :
              service_list.remove( serv )
          else:
              service = serv

        if len(self.tvshow) > 0:
            if service_list.count(def_tv_service) > 0:
                service = def_tv_service
            else:
                if service_list.count(def_service) > 0:
                    service = def_service
        else:
            if service_list.count(def_movie_service) > 0:
                service = def_movie_service
            else:
                if service_list.count(def_service) > 0:
                    service = def_service

        if len(service_list) > 0:  
            if len(service) < 1:
              self.service = service_list[0]
            else:
              self.service = service  
              
            self.service_list = service_list
            self.controlId = -1
            self.shufle = 0
            self.subtitles_list = []
            
            log( __name__ ,"Manual Search : [%s]"        % self.mansearch)
            log( __name__ ,"Default Service : [%s]"      % self.service)
            log( __name__ ,"Services : [%s]"             % self.service_list)
            log( __name__ ,"Temp?: [%s]"                 % self.set_temp)
            log( __name__ ,"File Path: [%s]"             % self.file_original_path)
            log( __name__ ,"Year: [%s]"                  % str(self.year))
            log( __name__ ,"Tv Show Title: [%s]"         % self.tvshow)
            log( __name__ ,"Tv Show Season: [%s]"        % self.season)
            log( __name__ ,"Tv Show Episode: [%s]"       % self.episode)
            log( __name__ ,"Movie/Episode Title: [%s]"   % self.title)
            log( __name__ ,"Subtitle Folder: [%s]"       % self.sub_folder)
            log( __name__ ,"Languages: [%s] [%s] [%s]"   % (self.language_1, self.language_2, self.language_3,))
            log( __name__ ,"Parent Folder Search: [%s]"  % self.parsearch)
            try:
                self.Search_Subtitles()
            except:
                errno, errstr = sys.exc_info()[:2]
                self.getControl( STATUS_LABEL ).setLabel( "Error:" + " " + str(errstr) )
                xbmc.sleep(2000)
                self.exit_script()
        else:
            self.getControl( STATUS_LABEL ).setLabel( "No Services Have been selected" )
            xbmc.sleep(2000)
            self.exit_script()
            
       

#### ---------------------------- On Init ----------------------------###



    def onInit( self ):
        self.set_allparam()


###-------------------------- Search Subtitles -------------################

    def Search_Subtitles( self ):
        self.subtitles_list = []
        self.getControl( SUBTITLES_LIST ).reset()
        self.getControl( LOADING_IMAGE ).setImage( xbmc.translatePath( os.path.join( SERVICE_DIR, self.service, "logo.png") ) )
    
        exec ( "from services.%s import service as Service" % (self.service))
        self.Service = Service
        self.getControl( STATUS_LABEL ).setLabel( _( 646 ) )
        msg = ""

        log( __name__ ,"Socket timeout: %s" % (socket.getdefaulttimeout(),)  )
        log( __name__ ,"Timeout Setting: %s" % (__settings__.getSetting( "timeout" ),)  )
        
        socket.setdefaulttimeout(float(__settings__.getSetting( "timeout" )))
        log( __name__ ,"Socket timeout: %s" % (socket.getdefaulttimeout(),)  )
        
        try: 
            self.subtitles_list, self.session_id, msg = self.Service.search_subtitles( self.file_original_path, self.title, self.tvshow, self.year, self.season, self.episode, self.set_temp, self.rar, self.language_1, self.language_2, self.language_3 )
        except socket.error:
            errno, errstr = sys.exc_info()[:2]
            if errno == socket.timeout:
                msg = _( 656 )
            else:
                msg =  "%s: %s" % ( _( 653 ),str(errstr[1]), )
        except:
            errno, errstr = sys.exc_info()[:2]
            msg = "Error: %s" % ( str(errstr), )

        socket.setdefaulttimeout(None)

        log( __name__ ,"Socket timeout: %s" % (socket.getdefaulttimeout(),)  )
        
        self.getControl( STATUS_LABEL ).setLabel( _( 642 ) % ( "...", ) )

        if not self.subtitles_list: 
            if msg != "":
              self.getControl( STATUS_LABEL ).setLabel( msg )
            else:
              self.getControl( STATUS_LABEL ).setLabel( "No Subtitles Found!" )
            self.list_services()
    
        else:
            self.list_services()
            subscounter = 0
            for item in self.subtitles_list:
                listitem = xbmcgui.ListItem( label=item["language_name"], label2=item["filename"], iconImage=item["rating"], thumbnailImage=item["language_flag"] )
                if item["sync"]:
                    listitem.setProperty( "sync", "true" )
                else:
                    listitem.setProperty( "sync", "false" )
                self.list.append(subscounter)
                subscounter = subscounter + 1                                    
                self.getControl( SUBTITLES_LIST ).addItem( listitem )
    
            self.getControl( STATUS_LABEL ).setLabel( '%i %s '"' %s '"'' % (len ( self.subtitles_list ), _( 744 ), self.file_name,) ) 
        
        self.setFocus( self.getControl( SUBTITLES_LIST ) )
        self.getControl( SUBTITLES_LIST ).selectItem( 0 )

###-------------------------- Download Subtitles  -------------################

    def Download_Subtitles( self, pos ):
        self.getControl( STATUS_LABEL ).setLabel(  _( 649 ) )
        zip_subs = os.path.join( self.tmp_sub_dir, "zipsubs.zip")
        zipped, language, file = self.Service.download_subtitles(self.subtitles_list, pos, zip_subs, self.tmp_sub_dir, self.sub_folder,self.session_id)
        sub_lang = str(toOpenSubtitles_two(language))

        if zipped :
            self.Extract_Subtitles(zip_subs,sub_lang)
        else:
            sub_ext  = os.path.splitext( file )[1]
            sub_name = os.path.splitext( os.path.basename( self.file_original_path ) )[0]
            if (__settings__.getSetting( "lang_to_end" ) == "true"):
              file_name = "%s.%s%s" % ( sub_name, sub_lang, sub_ext )
            else:
              file_name = "%s%s" % ( sub_name, sub_ext )   
            file_path = os.path.join(self.sub_folder, file_name)
            shutil.copyfile(file, file_path)    
            xbmc.Player().setSubtitles(file_path)
            self.rem_files(self.tmp_sub_dir)
            self.exit_script()

###-------------------------- Extract, Rename & Activate Subtitles  -------------################    

    def Extract_Subtitles( self, zip_subs, subtitle_lang ):
        un = unzip.unzip()
        files = un.get_file_list( zip_subs )
        sub_filename = os.path.basename( self.file_original_path )
        exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]
        if len(files) < 1 :
            self.getControl( STATUS_LABEL ).setLabel( _( 654 ) )
            self.list_services()
        else :    
            self.getControl( STATUS_LABEL ).setLabel(  _( 652 ) )
            un.extract( zip_subs, self.tmp_sub_dir )
            subtitle_set = False
            movie_sub = False
            episode = 0
            for zip_entry in files:
                if os.path.splitext( zip_entry )[1] in exts:
                    subtitle_file, file_path = self.create_name(zip_entry,sub_filename,subtitle_lang)
                    if len(self.tvshow) > 0:
                        title, season, episode = regex_tvshow(False, zip_entry)
                        if not episode : episode = -1
                    else:
                        if os.path.splitext( zip_entry )[1] in exts:
                          movie_sub = True

                    if ( movie_sub or len(files) < 2 or int(episode) == int(self.episode) ):
                        subtitle_set,file_path = self.copy_files( subtitle_file, file_path )

            if not subtitle_set:
                for zip_entry in files:
                    if os.path.splitext( zip_entry )[1] in exts:
                        print os.path.splitext( zip_entry )[1]
                        subtitle_file, file_path = self.create_name(zip_entry,sub_filename,subtitle_lang)
                        subtitle_set,file_path  = self.copy_files( subtitle_file, file_path )            
        
        #self.rem_files((xbmc.translatePath(self.tmp_sub_dir))) # we dont want to clean now as there might be temporary subs activated. we clean on startup
        if subtitle_set :
          xbmc.Player().setSubtitles(file_path)
          self.exit_script()
        else:
          self.getControl( STATUS_LABEL ).setLabel( _( 654 ) )
          self.list_services()           

###-------------------------- Create name  -------------################

    def create_name(self,zip_entry,sub_filename,subtitle_lang):
        sub_ext  = os.path.splitext( zip_entry )[1]
        sub_name = os.path.splitext( sub_filename )[0]
        file_name = "%s.%s%s" % ( sub_name, subtitle_lang, sub_ext )   
        file_path = os.path.join(self.sub_folder, file_name)
        subtitle_file = os.path.join(self.tmp_sub_dir, zip_entry)
        return subtitle_file, file_path

###-------------------------- Copy files  -------------################
        
    def copy_files( self, subtitle_file, file_path ):
        subtitle_set = False
        try:
            shutil.copy(subtitle_file, file_path)
            subtitle_set = True
        except :
            import filecmp
            try:
                if filecmp.cmp(subtitle_file, file_path):
                    subtitle_set = True
            except:
                dialog = xbmcgui.Dialog( __name__ ,)
                selected = dialog.yesno( __scriptname__ , _( 748 ), _( 750 ),"" )
                if selected == 1:
                    file_path = subtitle_file
                    subtitle_set = True
            
        return subtitle_set, file_path


            
            
###-------------------------- List Available Services  -------------################

    def list_services( self ):
        
        service_list = self.service_list
        if self.shufle == 0:
           service_list.reverse()
           self.shufle = 1
        else:
           self.shufle = 0  

        self.getControl( SUBTITLES_LIST ).reset()
        label = ""
        self.list = []

        for serv in service_list:
            if serv != self.service:
              label2 = "[COLOR=FF%s]%s%s[/COLOR]"  %(self.label_colour,_( 610 ), serv,) 
              listitem = xbmcgui.ListItem( label,label2 )
              self.list.append(serv)
              self.getControl( SUBTITLES_LIST ).addItem( listitem )
        
        if self.mansearch :
            label2 = "[COLOR=FF00FF00]%s[/COLOR]" % (  _( 612 ) )
            listitem = xbmcgui.ListItem( label,label2 )
            self.list.append("Man")
            self.getControl( SUBTITLES_LIST ).addItem( listitem ) 

        if self.parsearch :
            label2 = "[COLOR=FF00FF00]%s[/COLOR]" % (  _( 747 ) )
            listitem = xbmcgui.ListItem( label,label2 )
            self.list.append("Par")
            self.getControl( SUBTITLES_LIST ).addItem( listitem )

###-------------------------- Manual search Keyboard  -------------################


    def keyboard(self, parent):
        dir, self.year = xbmc.getCleanMovieTitle(os.path.split(os.path.split(self.file_original_path)[0])[1])
        if self.rar:
            tmp_dir = os.path.split(os.path.split(os.path.split(self.file_original_path)[0])[0])[1]
            dir, self.year = xbmc.getCleanMovieTitle( tmp_dir )
        if not parent:
            kb = xbmc.Keyboard("%s ()" % (dir,), _( 751 ), False)
            text = self.file_name
            kb.doModal()
            if (kb.isConfirmed()): text, self.year = xbmc.getCleanMovieTitle(kb.getText())
            self.title = text
        else:
            self.title = dir   
        
        log( __name__ ,"Manual/Keyboard Entry: Title:[%s], Year: [%s]" % (self.title, self.year,))
        if self.year != "" :
            self.file_name = "%s (%s)" % (self.file_name, str(self.year),)
        else:
            self.file_name = self.title   
        self.tvshow = ""
        self.Search_Subtitles()

###-------------------------- Exit script  -------------################

                
    def exit_script( self, restart=False ):
        self.close()

###-------------------------- Click  -------------################



    def onClick( self, controlId ):
        selection = str(self.list[self.getControl( SUBTITLES_LIST ).getSelectedPosition()])
        log( __name__ ,"In 'On click' selected : [%s]" % (selection, )  )
        if selection.isdigit():
            log( __name__ , "Selected : [%s]" % (selection, )  )                               
            self.Download_Subtitles( int(selection) )
        else:
            if selection == "Man":
              self.keyboard(False)
            elif selection == "Par":
              self.keyboard(True)
            else:  
              self.service = selection
              self.Search_Subtitles()
                                                                                                                                   

###-------------------------- Remove temp files  -------------################        

    def rem_files( self, directory):
      try:
        for root, dirs, files in os.walk(directory, topdown=False):
          for items in dirs:
            shutil.rmtree(os.path.join(root, items), ignore_errors=True, onerror=None)
          for name in files:
            os.remove(os.path.join(root, name))
      except:
        try:
          for root, dirs, files in os.walk(directory, topdown=False):
            for items in dirs:
              shutil.rmtree(os.path.join(root, items).decode("utf-8"), ignore_errors=True, onerror=None)
            for name in files:
              os.remove(os.path.join(root, name).decode("utf-8"))
        except:
          pass 
       

###-------------------------- On Focus  -------------################
 
    
    def onFocus( self, controlId ):
        self.controlId = controlId

###-------------------------- "Esc" , "Back" button  -------------################
        
def onAction( self, action ):
    if ( action.getButtonCode() in CANCEL_DIALOG):
        self.exit_script()

