# -*- coding: UTF-8 -*-


################################################################################################################################
##
##    Enigma2 -- pzyP4T -- by pzy-co  (GNU GPL3)
##
##    Copyright (C) 2014  pzy-co
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
################################################################################################################################

from Plugins.Plugin import PluginDescriptor

# GUI (Screens)
from Screens.ChannelSelection import SimpleChannelSelection, EPGSelection
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.TimerEdit import TimerEditList
from Screens.TimerEntry import TimerLog
from Screens.VirtualKeyBoard import VirtualKeyBoard

# GUI (Components)
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.config import config, getConfigListEntry ,ConfigSubsection, ConfigSubDict, ConfigSelection, ConfigText, NoSave
from Components.ConfigList import ConfigListScreen,ConfigList
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.Sources.Event import Event
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.StaticText import StaticText
from Components.TimerList import TimerList
from Components.TimerSanityCheck import TimerSanityCheck

# Tools
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.FuzzyDate import FuzzyTime
from Tools.LoadPixmap import LoadPixmap
from Tools.XMLTools import stringToXML
from xml.etree.cElementTree import parse as xml_parser

from enigma import eListbox, eListboxPythonMultiContent, eTimer, gFont, getDesktop, eServiceReference, eServiceCenter, iServiceInformation, gRGB, eEPGCache, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_HALIGN_BLOCK, RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_WRAP
from ServiceReference import ServiceReference
from RecordTimer import  AFTEREVENT
from timer import TimerEntry
from skin import parseColor, parseFont, parseSize, parsePosition, loadSkin
from time import time, strftime, localtime
from os.path import exists

from re import search

sz_w = getDesktop(0).size().width()

try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import addAutotimerFromEvent #, addAutotimerFromService, addAutotimerFromSearchString
	pzyP4T_AutoTimerAvailable = True
except ImportError:
	pzyP4T_AutoTimerAvailable = False
	
try:
	from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
	pzyP4T_EPGSearchAvailable = True
except ImportError:
	pzyP4T_EPGSearchAvailable = False

try:
	from enigma import PACKAGE_VERSION
	major, minor, patch = [int(n) for n in PACKAGE_VERSION.split('.')]
	if major > 4 or (major == 4 and minor >= 2):
		#7080HD
		pzy_bln_DreamOS = True
	else:
		pzy_bln_DreamOS = False
except ImportError:
	#No Dreambox
	pzy_bln_DreamOS = False
	
	


###################################################################################################################################
###################################################################################################################################
###################################################################################################################################


PZYP4T_VERSION="pzyP4T v0.3.3"
PZYP4T_CONFIG_VERSION="v0.2"
PZYP4T_XML_CONFIG = "/etc/enigma2/pzyP4T.xml"
PZYP4T_PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/pzyP4T/"

pzyP4T_Icon = "pzyP4T.png"
pzyP4T_writeSettings = False

pzyP4Tsession = None
pzyP4Tautopoller = None

color_service = 0x008B008B #DarkMagenta
color_service_selected = 0x00FF00FF #Magenta

color_title = 0x00FFFFFF #White
color_title_selected = 0x00FFFF00 #Yellow

color_eventDesc = 0x00228B22 #ForestGreen
color_eventDesc_selected = 0x007CFC00 #Lawngreen

color_time = 0x00FFFFFF #White
color_time_selected  = 0x0000C8FF #cy
color_time_short = 0x000066FF #blue
color_time_short_selected  = 0x000066FF #blue
color_time_record = 0x00FFFFFF #white
color_time_record_selected = 0x00FFFF00 #yellow

color_tuner = 0x00FFFF66 #or/ye
color_tuner_selected = 0x00FFFF66 #or/ye
color_orbital = 0x00FFFF66 #or/ye
color_orbital_selected = 0x00FFFF66 #or/ye

color_eventeit = 0x00FFFF66 #or/ye
color_eventeit_selected = 0x00FFFF66 #or/ye

color_state_waiting = 0x00CD9B1D #Darkgoldenrod3
color_state_waiting_selected = 0x00FFD700 #Gold
color_state_waiting_long = 0x001E90FF # Dodger Blue
color_state_waiting_long_selected = 0x0000FFFF # Blue4
color_state_starting = 0x00008B8B #cyan4
color_state_starting_selected = 0x0000FFFF #cyan
color_state_running = 0x00696969 #Dimgray
color_state_running_selected = 0x00D3D3D3 #Lightgray
color_state_recording = 0x00FF0000 #Red
color_state_recording_selected = 0x00FF0000 #Red
color_state_finished = 0x00228B22 #ForestGreen
color_state_finished_selected = 0x0000FA9A #MediumSpringGreen
color_state_disabled = 0x00FF6A6A #Indianred
color_state_disabled_selected = 0x00FF6A6A #Indianred
color_state_unknown = 0x004682B4 #SteelBlue
color_state_unknown_selected = 0x0000F5FF #turquoise1

color_title_filter_disabled = 0x00FF69B4 #HotPink


pzyP4TfilterComponentList = []
pzyP4TsettingsComponent = None

pzyP4T_timerReminderAvailable = False

###################################################################################################################################
###################################################################################################################################
###################################################################################################################################


def Plugins(**kwargs):
	loadPluginSkin(kwargs["path"])
	l = [ 
	        #PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart),
	        PluginDescriptor(name=_("PzyP4T"), description=_("Priorities 4 Timers"), where = PluginDescriptor.WHERE_PLUGINMENU, icon=pzyP4T_Icon, fnc=main),
	        PluginDescriptor(name =_("Timer+"), description = _("Priorities 4 Timers"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc = menu)
	]
	return l


def main(session, **kwargs):
	session.open(PzyP4T)

	
def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("Timer+"), main, "pzyP4T", 15)]
	return []	


def loadSkinReal(skinPath):
	if exists(skinPath):
		print "[pzyP4T] Loading skin ", skinPath
		loadSkin(skinPath)


def loadPluginSkin(pluginPath):
	loadSkinReal(pluginPath + "/" + config.skin.primary_skin.value)
	if sz_w == 1920:
		loadSkinReal(pluginPath + "/skin_1080.xml")
	else:
		loadSkinReal(pluginPath + "/skin.xml")
	
	
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################


def pzyparseColor(str):
	if str[0] != '#':
		try:
			return colorNames[str]
		except:
			#raise SkinError("color '%s' must be #aarrggbb or valid named color" % (str))
			return None
	try:
		grgb = gRGB(int(str[1:], 0x10))
	except:
		return None
	return grgb #gRGB(int(str[1:], 0x10))


def e2color2hex(e2color="#00000000"): #aarrggbb or "black"
	col = None
	try:
		col = parseColor(e2color) #grgb
	except:
		return None
	return col.argb()


###################################################################################################################################
###################################################################################################################################
###################################################################################################################################

class Keypress2ascii:
	def __init__(self,on_keypressed=[],on_finished=[]):
		self.__timer = eTimer()
		
		if not pzy_bln_DreamOS:
			self.__timer.callback.append(self.__query)
		else:
			self.__timer_conn = self.__timer.timeout.connect(self.__query)
			
		self.on_keypressed=on_keypressed
		self.on_finished=on_finished
		
		self.keynumber = None
		self.keypresses = 0
		
		#rc
		self.keyindex = { 1 : [" ","*","#",'"',"1"],
		                  2 : ["A","B","C","2","Ä"],
		                  3 : ["D","E","F","3"],
		                  4 : ["G","H","I","4"],
		                  5 : ["J","K","L","5"],
		                  6 : ["M","N","O","6","Ö"],
		                  7 : ["P","Q","R","S","7"],
		                  8 : ["T","U","V","8","Ü"],
		                  9 : ["W","X","Y","Z","9"],
		                  0 : ["0"] }
		

	def setDict(self,dict):
		self.keyindex = dict
		
		
	def stop(self):
		self.__timer.stop()
		if not pzy_bln_DreamOS:
			if self.__query in self.__timer.callback:
				self.__timer.callback.remove(self.__query)
		else:
			del self.__timer_conn
			
		self.__timer = None
		self.on_keypressed = []
		self.on_finished = []


	def pressed(self,keynumber):
		if not self.keyindex.has_key(keynumber):
			return
		
		if keynumber == self.keynumber:
			if self.keypresses < len(self.keyindex.get(self.keynumber))-1:
				self.keypresses +=1
			else:
				self.keypresses = 0
		else:
			self.keypresses = 0
			self.keynumber = keynumber
		
		self.__timer.stop()	
		self.__timer.start(750) #ms delay
		str_ret = str(self.keyindex.get(self.keynumber)[self.keypresses])
		for fnc in self.on_keypressed:
			fnc(str_ret)
		
		
	def __query(self):
		if not self.keyindex.has_key(self.keynumber):
			self.keynumber = None
			return
		
		str_ret = str(self.keyindex.get(self.keynumber)[self.keypresses])
		self.keypresses = 0
		self.keynumber = None
		
		for fnc in self.on_finished:
			fnc(str_ret)
			
			
			
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################


class PzyP4T(TimerEditList):

	def __init__(self, session):
		global pzyP4T_timerReminderAvailable
		global pzyP4TsettingsComponent
		
		TimerEditList.__init__(self, session)
		self.session = session
		
		try:
			ref = ServiceReference(None)
			from RecordTimer import RecordTimerEntry
			r = RecordTimerEntry(ref,0,0,"TEST","",None,True,True)
			val = r.justremind
			val = None
			r = None
			pzyP4T_timerReminderAvailable = True
		except:
			pzyP4T_timerReminderAvailable = False
		print "[pzyP4T] Timer: Reminder Available: %s" %(pzyP4T_timerReminderAvailable)
			
		self["Event"] = Event()
		self["ServiceEvent"] = ServiceEvent()
		
		pzyP4TsettingsComponent = pzyP4TSettings()
		                
		self.numberFunctions={
		        0: self.zap2service,
		        1: self.remove_and_arrange_helper,
		        2: self.remove_ended_timers,
		        3: self.arrangeTimerList_helper,
		        4: self.forceTimerON,
		        "info":  self.open_PzyP4TChannelSelection,
		        5: self.addFilter_helper,
		        6: self.show_matching_timers,
		        "text": self.searchEPG,
			7: self.open_PzyP4TEPGSelection,
		        8: self.openTMDb,
		        9: self.openTVDb,
			#" "
			">": self.exportTimer2AutoTimer,
			#" "
		        "<": self.open_PzyP4TSetup
		}
			
		self._timerlist = PzyP4TTimerList(self.list)
		self["timerlist"] = self._timerlist
		
		self.bln_filteredit = False
		self.bln_woservice_ref = False
				
		self["PiPSetupActions"] = ActionMap(["PiPSetupActions"],
			{
		                "size+": self.open_PzyP4TEPGSelection,
		                "size-": self.open_pzyP4TFilterList
			}
		)		
		
		self["InfobarChannelSelection"] = ActionMap(["InfobarChannelSelection"],
			{
				"historyNext": self.exportTimer2AutoTimer,
		                "historyBack": self.open_PzyP4TSetup #open_PzyP4TEPGSelection
			}
		)
		
		self["TimerEditActions"] = ActionMap(["TimerEditActions"],
			{
		                "log": self.open_PzyP4TChannelSelection
			},-10
		)		
		
		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.open_PzyP4TChannelSelection
			}
		)
		
		self["MenuActions"] = ActionMap(["MenuActions"],
			{
				"menu": self.KeyMenu
			}
		)
		
		self["NumberActions"] = NumberActionMap(["NumberActions"],
			{
		                "0": self.keyNumberGlobal,
		                "1": self.keyNumberGlobal,
		                "2": self.keyNumberGlobal,
		                "3": self.keyNumberGlobal,
		                "4": self.keyNumberGlobal,
		                "5": self.keyNumberGlobal,
		                "6": self.keyNumberGlobal,
		                "7": self.keyNumberGlobal,
		                "8": self.keyNumberGlobal,
		                "9": self.keyNumberGlobal
			}
		)		

		self["VirtualKeyboardActions"] = ActionMap(["VirtualKeyboardActions"],
			{
				"showVirtualKeyboard": self.searchEPG
			}
		)		

		self.setTitle("Timer List")
		self.onFirstExecBegin.append(self.firststart)
		
		
	############################
	
	
	def ask_start_autotimer(self):
		self.session.openWithCallback(
	                self.menuCallback,
	                cbx,
	                title = "Start Autotimer EPG Parsing?",
	                list = [ 
	                        
		                (_("Yes"), self.ask_start_autotimer_yes),
		                (_("No"), self.ask_start_autotimer_no),
	                        ],
	                
	                keys = ["green", "red"]
	        )
		
		
	def ask_start_autotimer_no(self):
		self.autotimer_finished()
	
	
	def ask_start_autotimer_yes(self):
		try:
			from Plugins.Extensions.AutoTimer.plugin import autotimer
			if autotimer is None:
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()

			autotimer.parseEPGAsync(simulateOnly=False).addBoth(self.autotimer_finished)
			#return
		except Exception as e:
			print("[pzyP4T] AutoTimer Problem:", e)	
		self.autotimer_finished()
		
		
	def ask_remove_obsolete(self):
		self.session.openWithCallback(
	                self.menuCallback,
	                cbx,
	                title = "Remove Obsolete Timers?",
	                list = [ 
		                (_("Yes"), self.ask_remove_obsolete_yes),
	                        (_("No"), self.ask_remove_obsolete_no),
	                        ],
	                
	                keys = [ "green", "red"]
	        )
			
		
	def ask_remove_obsolete_yes(self):
		lst_obsolete = self.build_lst_obsolete()
		for t in lst_obsolete:
			timer = t[0]
			if not timer.isRunning() and not timer.repeated:
				timer.afterEvent = AFTEREVENT.NONE
				print "[pzyP4T] Timer Removed: %s > %s" %(timer.name,timer.description)
				self.session.nav.RecordTimer.removeEntry(timer)
		
		if len(lst_obsolete)>0:
			self.ask_start_autotimer()
		del lst_obsolete
		

	def ask_remove_obsolete_no(self):
		pass

	
	def remove_obsolete_timers(self,refill=True):
		self.ask_remove_obsolete()

	
	def build_seasons(self):
		lst = self.sortedTimers()
		rstr = "([0-9]+). %s, %s ([0-9]+):"%(_("Staffel"),_("Folge"))
		restr = eval('r"%s"'%(rstr))
		for t in lst:
			timer = t[0]	
			
			event = None
			if timer:
				event_id = None
				epgcache = eEPGCache.getInstance()
	
				if isinstance(timer.service_ref, str):
					ref = timer.service_ref
				else:
					ref = timer.service_ref.ref.toString()
					
				begin = timer.begin + config.recording.margin_before.value*60
				duration = (timer.end - begin - config.recording.margin_after.value*60) / 60
				if duration <= 0:
					duration = 30
				list = epgcache.lookupEvent([ 'IBDT', (ref, 0, begin, duration) ]) # [(eit, begin, duration, eventname)]
				
				if len(list) > 0:
					bln_eventname_ok = False
					if timer.eit:
						for epgevent in list:
							if epgevent[0] == long(timer.eit):
								event_id = epgevent[0]
	
					if event_id:
						event = epgcache.lookupEventId(timer.service_ref.ref, event_id)
						eventextendeddesc = event.getExtendedDescription()
						x = search(restr,eventextendeddesc)
						if x:
							season = x.group(1)
							if int(season) < 10:
								season = "0%s"%(season)
							episode = x.group(2)
							if int(episode) < 10:
								episode = "0%s"%(episode)
							se = "S%sE%s"%(season,episode)
							
							if timer.name.find(se) == -1:
								timer.name = "%s %s"%(timer.name,se)
								#print "%s %s"%(timer.name,se)
			self.__callback_refresh()
			
		
	def build_lst_obsolete(self):
		lst_obsolete = []
		lst = self.sortedTimers()	
		for t in lst:
			timer = t[0]
			if not self.getEPGEvent(timer, True): #remove_obsolete  True
				lst_obsolete.append(t)
		return lst_obsolete
		
		
	def getEPGEvent(self, timer,remove_obsolete=False):
		event = None
		if timer:
			event_id = None
			epgcache = eEPGCache.getInstance()

			if isinstance(timer.service_ref, str):
				ref = timer.service_ref
			else:
				ref = timer.service_ref.ref.toString()
				
			begin = timer.begin + config.recording.margin_before.value*60
			duration = (timer.end - begin - config.recording.margin_after.value*60) / 60
			if duration <= 0:
				duration = 30
			list = epgcache.lookupEvent([ 'IBDT', (ref, 0, begin, duration) ]) # [(eit, begin, duration, eventname)]
			
			if len(list) == 0:
				#print "[pzyP4T] No EPG CACHE Found To Check This Timer: %s > %s" %(timer.name,timer.description)
				if remove_obsolete:
					return True #maybe good event, we dont know
			else:
				bln_eventname_ok = False
				if timer.eit:
					for epgevent in list:
						if epgevent[0] == long(timer.eit):
							event_id = epgevent[0]
	
							#if timer.name.startswith(epgevent[3]):
							if timer.name.find(epgevent[3])>-1:
								bln_eventname_ok = True
							break
						
						# autotimer issue with eit correction 
						###elif timer.name.startswith(epgevent[3]) and epgevent[1] == long(timer.begin): #type int
						##elif timer.name.find(epgevent[3])>-1 and epgevent[1] == long(timer.begin): #type int
							##event_id = epgevent[0]
							##bln_eventname_ok = True
							##print "[pzyP4T] --------------------------------------------"
							##print "[pzyP4T] Timer.EIT Corrected: %s To %s -- %s > %s " %(timer.eit,event_id,timer.name,timer.description)
							##print "[pzyP4T] timer.begin: ", timer.begin,FuzzyTime(timer.begin)
							##print "[pzyP4T] --------------------------------------------"
							##timer.eit = event_id  # type long = long
							##break
						
				if event_id:
					event = epgcache.lookupEventId(timer.service_ref.ref, event_id)
					eventshortdesc = event.getShortDescription()
					if eventshortdesc != timer.description:
						if remove_obsolete and bln_eventname_ok:
							#print "[pzyP4T] --------------------------------------------"
							#print "[pzyP4T] Timer.description Corrected: %s \ntimer.description: %s \neventshortdesc: %s" %(timer.name, timer.description,eventshortdesc)
							#print "[pzyP4T] timer.begin: ", timer.begin,FuzzyTime(timer.begin)
							#print "[pzyP4T] --------------------------------------------"
							timer.description = eventshortdesc
							
				if not bln_eventname_ok:
					#print "[pzyP4T] --------------------------------------------"
					#print "[pzyP4T] OBSOLETE Timer:", timer.name
					#print "[pzyP4T] timer.description: ",timer.description
					#print "[pzyP4T] timer.begin: ", timer.begin,FuzzyTime(timer.begin)
					#print "[pzyP4T] timer.eit: ", timer.eit
					#print "[pzyP4T] event_id: ", event_id
					#print "[pzyP4T] epgcache.lookupEvent list: ",list
					#print "[pzyP4T] --------------------------------------------"
					if remove_obsolete:
						return False
		return event


	def autotimer_finished(self,data=None):
		try:
			self.refill()
			self.updateState()
		except:
			#we left the plugin
			pass
		
	
	
	def updateState(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			if self.key_red_choice != self.DELETE:
				self["actions"].actions.update({"red":self.removeTimerQuestion})
				self["key_red"].setText(_("Delete"))
				self.key_red_choice = self.DELETE
			
			if cur.disabled and (self.key_yellow_choice != self.ENABLE):
				self["actions"].actions.update({"yellow":self.toggleDisabledState})
				self["key_yellow"].setText(_("Enable"))
				self.key_yellow_choice = self.ENABLE
			elif cur.isRunning() and not cur.repeated and (self.key_yellow_choice != self.EMPTY):
				self.removeAction("yellow")
				self["key_yellow"].setText(" ")
				self.key_yellow_choice = self.EMPTY
			elif ((not cur.isRunning())or cur.repeated ) and (not cur.disabled) and (self.key_yellow_choice != self.DISABLE):
				self["actions"].actions.update({"yellow":self.toggleDisabledState})
				self["key_yellow"].setText(_("Disable"))
				self.key_yellow_choice = self.DISABLE
		else:
			if self.key_red_choice != self.EMPTY:
				self.removeAction("red")
				self["key_red"].setText(" ")
				self.key_red_choice = self.EMPTY
			if self.key_yellow_choice != self.EMPTY:
				self.removeAction("yellow")
				self["key_yellow"].setText(" ")
				self.key_yellow_choice = self.EMPTY
		
		showCleanup = True
		for x in self.list:
			if (not x[0].disabled) and (x[1] == True):
				break
		else:
			showCleanup = False
		
		if showCleanup and (self.key_blue_choice != self.CLEANUP):
			self["actions"].actions.update({"blue":self.cleanupQuestion})
			self["key_blue"].setText(_("Cleanup"))
			self.key_blue_choice = self.CLEANUP
		elif (not showCleanup) and (self.key_blue_choice != self.EMPTY):
			self.removeAction("blue")
			self["key_blue"].setText(" ")
			self.key_blue_choice = self.EMPTY

		event = self.getEPGEvent(cur)
		if event:
			self["Event"].newEvent(event)
			self["ServiceEvent"].newService(cur.service_ref.ref)
		else:
			self["Event"].newEvent(None)
			self["ServiceEvent"].newService(None)
				
				
	def openEventView(self):
		event = None
		timer = self["timerlist"].getCurrent()
		if timer:
			event = self.getEPGEvent(timer)
		if event:
			from Screens.EventView import EventViewSimple
			self.session.openWithCallback(self.refill, EventViewSimple, event, timer.service_ref)
			
		
############################


	def firststart(self):
		self._timerlist.moveToIndex(0)
		self.read_cfg()
			
		
	def KeyMenu(self):
		self.session.openWithCallback(
			self.menuCallback,
			cbx,
		        title = "Menu",
			list = [ 
		                (_("Zap 2 Service"), self.zap2service),
		                (_("Remove Ended Timers & Arrange TimerList"), self.remove_and_arrange_helper),
		                (_("Remove Ended Timers"), self.remove_ended_timers),
		                (_("Arrange TimerList"), self.arrangeTimerList_helper),
		                (_("Timer ON - Deactivate All Conflicts"), self.forceTimerON),
		                (_("Add Timer From EPG / Filters With 'Info/EPG'-Key"), self.open_PzyP4TChannelSelection),
		                (_("Add Filter From Timer"), self.addFilter_helper),
		                (_("Search EPG: Selected Event"), self.show_matching_timers),
		                (_("Search EPG: Similar Events"), self.searchEPG),
		                (_("Open EPG: Service"), self.open_PzyP4TEPGSelection),
		                (_("Search Event: TMDB Info (AMS)"), self.openTMDb),
		                (_("Search Event: TMDB Serie Info (AMS)"), self.openTMDbSerie),
		                (_("Search Event: TVDB Info (AMS)"), self.openTVDb),
		                (_("Search Event: ImdB"), self.openImdb),
		                (_("Search Event: SeriesPlugin"), self.openSP),
		                (_("Export Timer 2 Autotimer"), self.exportTimer2AutoTimer),
		                (_("Open Filter Priority Arrangement"), self.open_pzyP4TFilterList),
		                (_("Open Settings"), self.open_PzyP4TSetup),
		                (_("Open Timer Log"), self.open_TimerLog),
		                (_("Start Autotimer EPG Parsing"), self.ask_start_autotimer_yes),
		                (_("Build Clean Timerlist"), self.remove_obsolete_timers),
		                (_("Add Season From EPG"), self.build_seasons),
		                ],
		        
		        keys = [ "0", "1", "2", "3", "4", "info", "5", "6", "text", "7", "8", "9"]
		)		
	
		
	def menuCallback(self, ret):
		ret and ret[1]()
		
		
	def open_TimerLog(self):
		cur = self._timerlist.getCurrent()
		if cur:
			self.session.openWithCallback(self.__callback_refresh,PzyTimerLog,timer=cur)
		

	def keyNumberGlobal(self, number):
		if self.numberFunctions.has_key(number):
			fnc = self.numberFunctions.get(number)
			fnc()
			
		
	def show_matching_timers(self):
		#nur exakte Wiederholung
		
		timer = self["timerlist"].getCurrent()
		if timer:
			evt = self.getEPGEvent(timer)
			if evt:
				evt_id = evt.getEventId()
				if isinstance(timer.service_ref, str):
					ref = timer.service_ref
				else:
					ref = timer.service_ref.ref.toString()
					
				self.session.open(PzyP4TEPGSelection, ref, None, evt_id)
				
		
	def searchEPG(self, searchString = None, searchSave = True):
		#similar timers
		if not pzyP4T_EPGSearchAvailable:
			return
		
		timer = self._timerlist.getCurrent()
		if timer:
			self.session.openWithCallback(
		                self.__callback_refresh,
		                EPGSearch, 
		                timer.name
		        )	
			#def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):

			
	def exportTimer2AutoTimer(self):
		if pzyP4T_AutoTimerAvailable:
			recordtimerentry = self["timerlist"].getCurrent()
			if recordtimerentry is None:
				return
			evt = self.getEPGEvent(recordtimerentry)
			addAutotimerFromEvent(self.session, evt, recordtimerentry.service_ref.ref)

		
	def openImdb(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry is None:
			return
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, recordtimerentry.name)

		except ImportError as ie:
			pass
		

	def remove_and_arrange_helper(self):
		self.session.openWithCallback(
			self.menuCallback,
			cbx,
		        title = "Arrange Timerlist With Recordings Prefered?",
			list = [ 
		                ("Yes", self.remove_and_arrange_recordingsfirst),
		                ("No", self.remove_and_arrange)
		        ],
		        
		        keys = ["1", "2"]
		)		
		
		
	def remove_and_arrange(self):
		self.remove_ended_timers(refill=False)
		self.arrangeTimerList()
		
		
	def remove_and_arrange_recordingsfirst(self):
		self.remove_ended_timers(refill=False)
		self.arrangeTimerList_RecordingsPrefered()
		

	def addFilter_helper(self):	
		self.session.openWithCallback(
			self.menuCallback,
			cbx,
		        title = "Add Filter For All Services?",
			list = [ 
		                ("Yes", self.addFilterwoService),
		                ("No", self.addFilter)
		                ],
		        
		        keys = ["1", "2"]
		)		

		
	def addFilter(self,woservice_ref=False):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry:
			tpc = pzyP4TFilterComponent()
			
			tpc.disabled = False
			
			tpc.filterTitle = recordtimerentry.name
			tpc.searchString = recordtimerentry.name
			
			if woservice_ref:
				tpc.use_servicename = False
				tpc.show_servicename = False
			else:
				tpc.use_servicename = True
				tpc.show_servicename = False
			tpc.service_ref_name = recordtimerentry.service_ref.getServiceName()
		
			self.open_PzyP4TFilterEditor((tpc,0))
			
	
	def open_PzyP4TFilterEditor(self,filterComponent=None):
			self.session.openWithCallback(
				self.__back_open_PzyP4TFilterEditor,
				PzyP4TFilterEditor,
				cur_filterComponent=filterComponent
			)			
			
			
	def __back_open_PzyP4TFilterEditor(self,filterComponent=None):
		global pzyP4T_writeSettings
		
		if filterComponent:
			pzyP4TfilterComponentList.append((filterComponent,0))
			pzyP4T_writeSettings = True
		
		self.__callback_refresh()
	
			
	def addFilterwoService(self):	
		self.addFilter(True)
	
		
	def open_PzyP4TChannelSelection(self):
		self.session.openWithCallback(
		        self.__callback_refresh,
		        PzyP4TChannelSelection
		)
		
		
	def open_PzyP4TEPGSelection(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry:	
			self.session.openWithCallback(
			        self.__callback_refresh,
			        PzyP4TEPGSelection,
				recordtimerentry.service_ref.ref
			) 		

		
	def open_PzyP4TSetup(self):
		self.session.openWithCallback(
		        self.__callback_refresh,
		        PzyP4TSetup
		)
			

	def open_pzyP4TFilterList(self):
		self.session.openWithCallback(
	                self.__callback_refresh,
	                pzyP4TFilterList
	        )
		
		
	def __callback_refresh(self,ref=None):
		self.refill()
		self.updateState()
		

	def openTMDb(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry is None:
			return
		
		try:
			from Plugins.Extensions.TMDb.plugin import TMDbMain
			self.session.open(TMDbMain, recordtimerentry.name)
			
		except ImportError as ie:
			try:
				from Plugins.Extensions.AdvancedMovieSelection.plugin import tmdbInfo
				tmdbInfo(self.session, recordtimerentry.name)
		
			except ImportError as ie:
				pass
			
	def openTMDbSerie(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry is None:
			return
		
		try:
			from Plugins.Extensions.AdvancedMovieSelection.plugin import tmdbSeriesInfo
			tmdbSeriesInfo(self.session, recordtimerentry.name)
		
		except ImportError as ie:
			pass
				
						
	def openTVDb(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry is None:
			return
		
		try:
			from Plugins.Extensions.TheTVDB.plugin import TheTVDBMain
			self.session.open(TheTVDBMain, recordtimerentry.name)

		except ImportError as ie:
			try:
				from Plugins.Extensions.AdvancedMovieSelection.plugin import tvdbInfo
				tvdbInfo(self.session, recordtimerentry.name)
			
			except ImportError as ie:
				pass
			
			
		
		
	def openSP(self):
		try:
			from Plugins.Extensions.SeriesPlugin.SeriesPluginInfoScreen import SeriesPluginInfoScreen

		except ImportError as ie:
			return
		
		service = self["ServiceEvent"].getCurrentService()
		event = self["Event"].getCurrentEvent()
		
		if service and event:
			self.session.open(SeriesPluginInfoScreen, service, event)
				
		
	def zap2service(self):
		recordtimerentry = self["timerlist"].getCurrent()
		if recordtimerentry:
			self.oldservice = self.session.nav.getCurrentlyPlayingServiceReference()
			try:
				self.session.nav.playService(recordtimerentry.service_ref.ref)
			except:
				self.session.nav.playService(self.oldservice)


	def filtertimers_off(self):	
		#recordtimerentry
		#tpc=pzyP4TFilterComponent() #test
	
		for tpc,idx in pzyP4TfilterComponentList:
			for t in self.list:
				timer = t[0]
				
				if not pzyP4T_timerReminderAvailable:
					#patch for dreambox, important
					#RecordTimerEntry has no '.justremind'
					timer.justremind = timer.justplay
					
				if not timer.disabled and timer.begin > self._timerlist.now:
					if tpc.case_insensitive:
						tpcsearchString = tpc.searchString.lower()
						timer_name_lower = timer.name.lower()
					else:
						tpcsearchString = tpc.searchString
						timer_name_lower = timer.name
						
					timer_name_lower_ok = False
					if tpc.searchpart:
						if tpcsearchString in timer_name_lower:
							timer_name_lower_ok = True
					else:
						if tpcsearchString == timer_name_lower:
							timer_name_lower_ok = True
						
					if timer_name_lower_ok:
						if not tpc.use_servicename or tpc.service_ref_name == "" or timer.service_ref.getServiceName() == tpc.service_ref_name:
							if (timer.justplay and tpc.justplay or timer.justremind and tpc.justremind) or (tpc.justremind and tpc.justremind and tpc.justrecord): #Spezialfall für Filter, alle .just* TRUE  and not timer.isRunning():
								timer.disable()
								self.session.nav.RecordTimer.timeChanged(timer)
							else:
								#recordings
								if tpc.justrecord and not timer.isRunning():
									timer.disable()
									self.session.nav.RecordTimer.timeChanged(timer)
									
			
									
	def sortedTimers(self):
		if config.usage.timerlist_finished_timer_position.index:
			lst = self.list[:]
			lst.sort(key = lambda x: x[0].begin)
		
		else:
			lst = self.list
		
		return lst


	def filtertimers_on(self):
		lst = self.sortedTimers()
		
		for tpc,idx in pzyP4TfilterComponentList:
			lastend=0
			
			for t in lst:
				timer = t[0]

				if not pzyP4T_timerReminderAvailable:
					#patch for dreambox, important
					#RecordTimerEntry has no '.justremind'
					timer.justremind = timer.justplay
				
				if timer.justremind and tpc.justremind or timer.justplay and tpc.justplay or (tpc.justremind and tpc.justremind and tpc.justrecord): #Spezialfall für Filter, alle .just* TRUE
					if timer.disabled and timer.begin > self._timerlist.now:
						if tpc.case_insensitive:
							tpcsearchString = tpc.searchString.lower()
							timer_name_lower = timer.name.lower()
						else:
							tpcsearchString = tpc.searchString
							timer_name_lower = timer.name
							
						timer_name_lower_ok = False
						if tpc.searchpart:
							if tpcsearchString in timer_name_lower:
								timer_name_lower_ok = True
						else:
							if tpcsearchString == timer_name_lower:
								timer_name_lower_ok = True
							
						if timer_name_lower_ok:	
							if not tpc.use_servicename or tpc.service_ref_name == "" or timer.service_ref.getServiceName() == tpc.service_ref_name:
								if timer.begin >= lastend:
									timer.enable()
									timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, timer)
								
									if not timersanitycheck.check():
										timer.disable()
										print "Sanity check failed"
										#simulTimerList = timersanitycheck.getSimulTimerList()
										#if simulTimerList is not None:
											#self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, simulTimerList)
									else:
										print "Sanity check passed"
										if timersanitycheck.doubleCheck():
											timer.disable()
										else:
											try:
												self.session.nav.RecordTimer.timeChanged(timer)
											except:
												pass

				if not timer.disabled and timer.begin > self._timerlist.now:
					lastend=timer.end


	def filtertimers_recordings_on(self):
		lst = self.sortedTimers()
		
		for tpc,idx in pzyP4TfilterComponentList:
			lastend=0
			for t in lst:
				timer = t[0]
				
				if not pzyP4T_timerReminderAvailable:
					#patch for dreambox, important
					#RecordTimerEntry has no '.justremind'
					timer.justremind = timer.justplay
					
				if not timer.justremind and not tpc.justremind and not timer.justplay and not tpc.justplay or ((not timer.justremind and not timer.justplay) and (tpc.justremind and tpc.justremind and tpc.justrecord)): #Spezialfall, nur im Filter
					if timer.disabled and timer.begin > self._timerlist.now:
						if not timer.justplay and not timer.justremind:
							if tpc.case_insensitive:
								tpcsearchString = tpc.searchString.lower()
								timer_name_lower = timer.name.lower()
							else:
								tpcsearchString = tpc.searchString
								timer_name_lower = timer.name
								
							timer_name_lower_ok = False
							if tpc.searchpart:
								if tpcsearchString in timer_name_lower:
									timer_name_lower_ok = True
							else:
								if tpcsearchString == timer_name_lower:
									timer_name_lower_ok = True
								
							if timer_name_lower_ok:		
								if not tpc.use_servicename or tpc.service_ref_name == "" or timer.service_ref.getServiceName() == tpc.service_ref_name: ##service_ref_name.lower()
									if timer.begin >= lastend:	
										timer.enable()
										timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, timer)
									
										if not timersanitycheck.check():
											timer.disable()
											print "Sanity check failed"
											#simulTimerList = timersanitycheck.getSimulTimerList()
											#if simulTimerList is not None:
												#self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, simulTimerList)
										else:
											print "Sanity check passed"
											if timersanitycheck.doubleCheck():
												timer.disable()
											else:
												try:
													self.session.nav.RecordTimer.timeChanged(timer)
												except:
													pass
				if not timer.disabled and timer.begin > self._timerlist.now:
					lastend=timer.end
					
					
	def arrangeTimerList_helper(self):
		self.session.openWithCallback(
			self.menuCallback,
			cbx,
		        title = "Arrange Timerlist With Recordings Prefered?",
			list = [ 
		                ("Yes", self.arrangeTimerList_RecordingsPrefered),
		                ("No", self.arrangeTimerList)
		                ],
		        
		        keys = ["1", "2"]
		)
		
	
	def arrangeTimerList(self):
		self.arrangeTimerList_RecordingsPrefered(False)

		
	def arrangeTimerList_RecordingsPrefered(self,prefered=True):
		self._timerlist.now = int(time())
				
		self.filtertimers_off()
		if prefered:
			self.filtertimers_recordings_on()
		self.filtertimers_on()

		self.refill()
		
		#######
		#replace 2nd run with prev, next parsing
		self.filtertimers_off()
		if prefered:
			self.filtertimers_recordings_on()
		self.filtertimers_on()

		self.refill()
		self.updateState()	
		
		
	def forceTimerON(self):
		#recordtimerentry
		
		list = self["timerlist"]
		timer = list.getCurrent() 
		
		for i in range(1,3,1):
			if timer and timer.disabled:
				now = int(time())
				self._timerlist.now = now
			
				timer.enable()
				timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, timer)
				
				timersanitycheckpassed = False
				if not timersanitycheck.check():
					#timer.disable()
					print "Sanity check failed, processing SimulTimerList"
					simulTimerList = timersanitycheck.getSimulTimerList()
					if simulTimerList is not None:
						#self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, simulTimerList)
						for t in simulTimerList:
							t.disable()
							try:
								self.session.nav.RecordTimer.timeChanged(t)
							except:
								print "[pzyP4T] self.session.nav.RecordTimer.timeChanged ERROR in:",repr(t)
					if not timersanitycheck.check():
						timer.disable()
					else:
						timersanitycheckpassed = True
				else:
					timersanitycheckpassed = True
				
				if timersanitycheckpassed:
					print "Sanity check passed"
					if timersanitycheck.doubleCheck():
						timer.disable()
				try:
					self.session.nav.RecordTimer.timeChanged(timer)
				except:
					pass		
				self.refill()
				self.updateState()
		
		####
		idx = 0
		for x in self.list:
			if x[0] == timer:
				list.moveToIndex(idx) 
				break
			idx += 1	
		self.refill()
		self.updateState()		
		
		
	def remove_ended_timers(self,refill=True):
		lst = self.sortedTimers()	
		
		now = int(time())
		self._timerlist.now = now
		for t in lst:
			timer = t[0]
			if timer.begin > now:
				break
			
			if timer.end < now and not timer.isRunning() and not timer.repeated:
				timer.afterEvent = AFTEREVENT.NONE
				self.session.nav.RecordTimer.removeEntry(timer)
		if refill:
			self.refill()
			self.updateState()
		#self.cleanupTimer(True) #bad
		

	def read_cfg(self):
		global pzyP4TfilterComponentList
		
		global color_title
		global color_title_selected
		global color_title_filter_disabled
		global color_eventDesc
		global color_eventDesc_selected
		global color_service
		global color_service_selected
		global color_time
		global color_time_selected
		global color_time_short
		global color_time_short_selected
		global color_time_record
		global color_time_record_selected
		
		global color_tuner
		global color_tuner_selected
		global color_orbital
		global color_orbital_selected
		
		global color_eventeit
		global color_eventeit_selected
		
		global color_state_waiting
		global color_state_waiting_selected
		global color_state_waiting_long
		global color_state_waiting_long_selected
		global color_state_starting
		global color_state_starting_selected
		global color_state_running
		global color_state_running_selected
		global color_state_recording
		global color_state_recording_selected
		global color_state_finished
		global color_state_finished_selected
		global color_state_disabled
		global color_state_disabled_selected
		global color_state_unknown	
		global color_state_unknown_selected
		global pzyP4TsettingsComponent
		
		
		xmlc = xmlconfig()
		st = xmlc.readXml()
		
		s = pzyP4TsettingsComponent
		pzyP4TfilterComponentList = s.filterComponentList
		
		if not s.use_skin_colors:
			color_title = e2color2hex(s.color_title)
			color_title_selected = e2color2hex(s.color_title_selected)
			color_title_filter_disabled = e2color2hex(s.color_title_filter_disabled)
			color_eventDesc = e2color2hex(s.color_eventDesc)
			color_eventDesc_selected = e2color2hex(s.color_eventDesc_selected)
			color_service = e2color2hex(s.color_service)
			color_service_selected = e2color2hex(s.color_service_selected)
			color_time = e2color2hex(s.color_time)
			color_time_selected = e2color2hex(s.color_time_selected)
			color_time_short = e2color2hex(s.color_time_short)
			color_time_short_selected = e2color2hex(s.color_time_short_selected)
			color_time_record = e2color2hex(s.color_time_record)
			color_time_record_selected = e2color2hex(s.color_time_record_selected)
			
			color_tuner = e2color2hex(s.color_tuner)
			color_tuner_selected = e2color2hex(s.color_tuner_selected)
			color_orbital = e2color2hex(s.color_orbital)
			color_orbital_selected = e2color2hex(s.color_orbital_selected)
			
			color_eventeit = e2color2hex(s.color_eventeit)
			color_eventeit_selected = e2color2hex(s.color_eventeit_selected)
			
			color_state_waiting = e2color2hex(s.color_state_waiting)
			color_state_waiting_selected = e2color2hex(s.color_state_waiting_selected)
			color_state_waiting_long = e2color2hex(s.color_state_waiting_long)
			color_state_waiting_long_selected = e2color2hex(s.color_state_waiting_long_selected)
			color_state_starting = e2color2hex(s.color_state_starting)
			color_state_starting_selected = e2color2hex(s.color_state_starting_selected)
			color_state_running = e2color2hex(s.color_state_running)
			color_state_running_selected = e2color2hex(s.color_state_running_selected)
			color_state_recording = e2color2hex(s.color_state_recording)
			color_state_recording_selected = e2color2hex(s.color_state_recording_selected)
			color_state_finished = e2color2hex(s.color_state_finished)
			color_state_finished_selected = e2color2hex(s.color_state_finished_selected)
			color_state_disabled = e2color2hex(s.color_state_disabled)
			color_state_disabled_selected = e2color2hex(s.color_state_disabled_selected)
			color_state_unknown = e2color2hex(s.color_state_unknown)
			color_state_unknown_selected = e2color2hex(s.color_state_unknown_selected)

			
	def write_cfg(self):
		global pzyP4T_writeSettings
		global pzyP4TsettingsComponent
		
		if not exists (PZYP4T_XML_CONFIG):
			pzyP4T_writeSettings = True
		
		if pzyP4T_writeSettings:
			pzyP4T_writeSettings = False
			
			xmlc = xmlconfig()
			xmlc.writeXml()
			

	def leave(self):
		global pzyP4TfilterComponentList
		global pzyP4TsettingsComponent
		global pzyP4Tsession
		
		self.session.nav.RecordTimer.on_state_change.remove(self.onStateChange)
		self.write_cfg()
		pzyP4Tsession = None
		pzyP4TfilterComponentList = None
		pzyP4TsettingsComponent = None
		
		self.close()
		
		
###################################################################################################################################


class PzyP4TTimerList(HTMLComponent, GUIComponent, object):
	# ColorTimerList in PzyP4T
	
	def __init__(self, list, markPriorityTimers=True):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()

		self.l.setFont(0, gFont("Regular", 18)) #service
		self.l.setFont(1, gFont("Regular", 20)) #event
		self.l.setFont(2, gFont("Regular", 18)) #time
		self.l.setFont(3, gFont("Regular", 18)) #state
		self.l.setFont(4, gFont("Regular", 16)) #eventDesc
		self.l.setFont(5, gFont("Regular", 10)) #tuner_type
		self.l.setFont(6, gFont("Regular", 10)) #orbital_pos
		self.l.setFont(7, gFont("Regular", 10)) #eventeit
		self.l.setItemHeight(70)
		
		self.running_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_red.png"))
		self.finished_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_green.png"))
		self.waiting_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_yellow.png"))
		self.waiting_timer_long = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_blue.png"))
		self.disabled_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_blue.png"))
		self.disabled_timer_x = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/disabled_timer.png"))
		self.repeat_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/repeat_timer.png"))
		self.instant_record = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/instant_record.png"))
		self.zap_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/zaptimer.png"))
		
		self.x_service = 0
		self.x_event = 0
		self.x_eventDesc = 200
		self.x_time = 0
		self.x_state = 520
		self.x_tuner = 0
		self.x_orbital = 0
		self.x_eventeit = 5
		self.y_service = 0
		self.y_event = 20
		self.y_eventDesc = 5
		self.y_time = 45
		self.y_state = 45
		self.y_tuner = 3
		self.y_orbital = 24
		self.y_eventeit = 50
		
		self.x_service_icons = 40
		self.x_event_icons = 40
		self.x_eventDesc_icons = 40
		self.x_time_icons = 40
		self.x_state_icons = 520 
		self.x_tuner_icons = 0
		self.x_orbital_icons = 0
		self.x_eventeit_icons = 0
		self.y_service_icons = 0
		self.y_event_icons = 20
		self.y_eventDesc_icons = 20
		self.y_time_icons = 45
		self.y_state_icons = 45
		self.y_tuner_icons = 3
		self.y_orbital_icons = 47
		self.y_eventeit_icons = 3
		
		self.width_service = 560
		self.width_event = 560
		self.width_eventDesc = 470
		self.width_time = 560
		self.width_state = 150
		self.width_tuner = 40
		self.width_orbital = 40
		self.width_eventeit = 250
		
		self.height_state = 20
		self.height_service = 20
		self.height_event = 30
		self.height_eventDesc = 0
		self.height_time = 20
		self.height_tuner = 20
		self.height_orbital = 20
		self.height_eventeit = 30

		self.timericon_pos_x = 0
		self.timericon_pos_y = 0
		self.timericon_width = 40
		self.timericon_height = 40
		
		self.zapicon_pos_x = 0
		self.zapicon_pos_y = 20	
		self.zapicon_width = 40
		self.zapicon_height = 40
		
		self.repeaticon_pos_x = 0
		self.repeaticon_pos_y = 35
		self.repeaticon_width = 40
		self.repeaticon_height = 40
		
		self.disabledicon_pos_x = 520
		self.disabledicon_pos_y = 15
		self.disabledicon_pos_x_icons = 0
		self.disabledicon_pos_y_icons = 15
		
		self.disabledicon_width = 40
		self.disabledicon_height = 40
		
		self.recicon_pos_x = 0
		self.recicon_pos_y = 15
		self.recicon_width = 40
		self.recicon_height = 40
		
		self.finishedicon_pos_x = 0
		self.finishedicon_pos_y = 35
		self.finishedicon_width = 40
		self.finishedicon_height = 40
		
		self.runningicon_pos_x = 0
		self.runningicon_pos_y = 15		
		self.runningicon_width = 40
		self.runningicon_height = 40
		
		self.service_align = RT_HALIGN_LEFT|RT_VALIGN_CENTER
		self.event_align = RT_HALIGN_LEFT|RT_VALIGN_CENTER
		self.eventDesc_align = RT_HALIGN_RIGHT|RT_VALIGN_TOP
		self.time_align = RT_HALIGN_LEFT|RT_VALIGN_CENTER
		self.state_align = RT_HALIGN_RIGHT|RT_VALIGN_CENTER
		self.tuner_align = RT_HALIGN_CENTER|RT_VALIGN_CENTER
		self.orbital_align = RT_HALIGN_CENTER|RT_VALIGN_CENTER
		self.eventeit_align = RT_HALIGN_LEFT|RT_VALIGN_CENTER
		
		self.use_uniForegroundSelected = False
					
		# load icons in cache to show them without restart
		self.running_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_running.svg"))
		self.finished_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_finished.svg"))
		self.waiting_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_waiting.svg"))
		self.waiting_timer_long = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_waiting_long.svg"))
		self.disabled_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_disabled.svg"))
		self.repeat_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_repeat.svg"))
		self.instant_record = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_instant_rec.svg"))
		self.zap_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_zap.svg"))

		if self.running_timer is None:
			self.running_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_running.png"))
		if self.finished_timer is None:
			self.finished_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_finished.png"))
		if self.waiting_timer is None:
			self.waiting_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_waiting.png"))
		if self.waiting_timer_long is None:
			self.waiting_timer_long = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_waiting_long.png"))
		if self.repeat_timer is None:
			self.repeat_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_repeat.png"))
		if self.instant_record is None:
			self.instant_record = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_instant_rec.png"))
		if self.zap_timer is None:
			self.zap_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_zap.png"))		
		if self.disabled_timer is None:
			self.disabled_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/timerlist_disabled.png"))

		if self.running_timer is None:
			self.running_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_play.png"))
		if self.finished_timer is None:
			self.finished_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))
		if self.waiting_timer is None:
			self.waiting_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/epgclock.png"))
		if self.waiting_timer_long is None:
			self.waiting_timer_long = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/epgclock_pre.png"))
		if self.repeat_timer is None:
			self.repeat_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/repeat_on.png"))
		if self.instant_record is None:
			self.instant_record = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/icon_rec.png"))
		if self.zap_timer is None:
			self.zap_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/icon_view.png"))		
		if self.disabled_timer is None:
			self.disabled_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/redx.png"))


		self.markPriorityTimers = markPriorityTimers
		self.now = int(time())
		self.l.setBuildFunc(self.buildColorTimerEntry)
		self._list = list
		self.l.setList(self._list)

	def getList(self):
		return self._list

	def setList(self, lst):
		self._list = lst
		self.l.setList(self._list)

	list = property(getList, setList)

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def invalidate(self):
		self.l.invalidate()

	def entryRemoved(self, idx):
		self.l.entryRemoved(idx)		

	def applySkin(self, desktop, parent):
		global color_title
		global color_title_selected
		global color_title_filter_disabled
		global color_eventDesc
		global color_eventDesc_selected
		global color_service
		global color_service_selected
		global color_time
		global color_time_selected
		global color_time_short
		global color_time_short_selected
		global color_time_record
		global color_time_record_selected
		global color_tuner
		global color_tuner_selected
		global color_orbital
		global color_orbital_selected
		global color_eventeit
		global color_eventeit_selected
		global color_state_waiting
		global color_state_waiting_selected
		global color_state_waiting_long
		global color_state_waiting_long_selected
		global color_state_starting
		global color_state_starting_selected
		global color_state_running
		global color_state_running_selected
		global color_state_recording
		global color_state_recording_selected
		global color_state_finished
		global color_state_finished_selected
		global color_state_disabled
		global color_state_disabled_selected
		global color_state_unknown
		global color_state_unknown_selected

		
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "service_font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "event_font":
					self.l.setFont(1, parseFont(value, ((1,1),(1,1))))
				elif attrib == "eventDescription_font":
					self.l.setFont(4, parseFont(value, ((1,1),(1,1))))
				elif attrib == "time_font":
					self.l.setFont(2, parseFont(value, ((1,1),(1,1))))
				elif attrib == "state_font":
					self.l.setFont(3, parseFont(value, ((1,1),(1,1))))
				elif attrib == "tuner_font":
					self.l.setFont(5, parseFont(value, ((1,1),(1,1))))
				elif attrib == "orbital_font":
					self.l.setFont(6, parseFont(value, ((1,1),(1,1))))
				elif attrib == "eventeit_font":
					self.l.setFont(7, parseFont(value, ((1,1),(1,1))))

				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "event_color":
					color_title = parseColor(value).argb()
				elif attrib == "event_color_selected":
					color_title_selected = parseColor(value).argb()
				elif attrib == "eventDescription_color":
					color_eventDesc = parseColor(value).argb()
				elif attrib == "eventDescription_color_selected":
					color_eventDesc_selected = parseColor(value).argb()
				elif attrib == "service_color":
					color_service = parseColor(value).argb()
				elif attrib == "service_color_selected":
					color_service_selected = parseColor(value).argb()
				elif attrib == "time_color":
					color_time = parseColor(value).argb()
				elif attrib == "time_color_selected":
					color_time_selected = parseColor(value).argb()
				elif attrib == "time_color_wo_endtime":
					color_time_short = parseColor(value).argb()
				elif attrib == "time_color_wo_endtime_selected":
					color_time_short_selected = parseColor(value).argb()
				elif attrib == "time_color_rec":
					color_time_record = parseColor(value).argb()
				elif attrib == "time_color_rec_selected":
					color_time_record_selected = parseColor(value).argb()
				
				elif attrib == "tuner_color":
					color_tuner = parseColor(value).argb()
				elif attrib == "tuner_color_selected":
					color_tuner_selected = parseColor(value).argb()
				elif attrib == "orbital_color":
					color_orbital = parseColor(value).argb()
				elif attrib == "orbital_color_selected":
					color_orbital_selected = parseColor(value).argb()
				elif attrib == "eventeit_color":
					color_eventeit = parseColor(value).argb()
				elif attrib == "eventeit_color_selected":
					color_eventeit_selected = parseColor(value).argb()
				
				elif attrib == "state_color_wait":
					color_state_waiting = parseColor(value).argb()
				elif attrib == "state_color_wait_selected":
					color_state_waiting_selected = parseColor(value).argb()
				elif attrib == "state_color_wait_long":
					color_state_waiting_long = parseColor(value).argb()
				elif attrib == "state_color_wait_long_selected":
					color_state_waiting_long_selected = parseColor(value).argb()
				elif attrib == "state_color_start":
					color_state_starting = parseColor(value).argb()
				elif attrib == "state_color_start_selected":
					color_state_starting_selected = parseColor(value).argb()
				elif attrib == "state_color_run":
					color_state_running = parseColor(value).argb()
				elif attrib == "state_color_run_selected":
					color_state_running_selected = parseColor(value).argb()
				elif attrib == "state_color_rec":
					color_state_recording = parseColor(value).argb()
				elif attrib == "state_color_rec_selected":
					color_state_recording_selected = parseColor(value).argb()
				elif attrib == "state_color_fin":
					color_state_finished = parseColor(value).argb()
				elif attrib == "state_color_fin_selected":
					color_state_finished_selected = parseColor(value).argb()
				elif attrib == "state_color_dis":
					color_state_disabled = parseColor(value).argb()
				elif attrib == "state_color_dis_selected":
					color_state_disabled_selected = parseColor(value).argb()
				elif attrib == "state_color_unknown":
					color_state_unknown = parseColor(value).argb()
				elif attrib == "state_color_unknown_selected":
					color_state_unknown_selected = parseColor(value).argb()
				elif attrib == "service_align":
					self.service_align = eval(value)
				elif attrib == "event_align":
					self.event_align = eval(value)
				elif attrib == "eventDescription_align":
					self.eventDesc_align = eval(value)
				elif attrib == "time_align":
					self.time_align = eval(value)
				elif attrib == "state_align":
					self.state_align = eval(value)
				elif attrib == "tuner_align":
					self.tuner_align = eval(value)
				elif attrib == "orbital_align":
					self.orbital_align = eval(value)
				elif attrib == "eventeit_align":
					self.eventeit_align = eval(value)
				elif attrib == "service_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_service = int(ep.x())
					self.y_service = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_service_icons = int(ep.x())
					self.y_service_icons = int(ep.y())
				elif attrib == "event_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_event = int(ep.x())
					self.y_event = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_event_icons = int(ep.x())
					self.y_event_icons = int(ep.y())
				elif attrib == "eventDescription_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_eventDesc = int(ep.x())
					self.y_eventDesc = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_eventDesc_icons = int(ep.x())
					self.y_eventDesc_icons = int(ep.y())
				elif attrib == "time_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_time = int(ep.x())
					self.y_time = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_time_icons = int(ep.x())
					self.y_time_icons = int(ep.y())	
				elif attrib == "state_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_state = int(ep.x())
					self.y_state = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_state_icons = int(ep.x())
					self.y_state_icons = int(ep.y())
				elif attrib == "tuner_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_tuner = int(ep.x())
					self.y_tuner = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_tuner_icons = int(ep.x())
					self.y_tuner_icons = int(ep.y())
				elif attrib == "orbital_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_orbital = int(ep.x())
					self.y_orbital = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_orbital_icons = int(ep.x())
					self.y_orbital_icons = int(ep.y())
				elif attrib == "eventeit_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.x_eventeit = int(ep.x())
					self.y_eventeit = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.x_eventeit_icons = int(ep.x())
					self.y_eventeit_icons = int(ep.y())
				elif attrib == "service_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_service = int(es.width())
					self.height_service = int(es.height())
				elif attrib == "event_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_event = int(es.width())
					self.height_event = int(es.height())
				elif attrib == "eventDescription_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_eventDesc = int(es.width())
					self.height_eventDesc = int(es.height())
				elif attrib == "time_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_time = int(es.width())
					self.height_time = int(es.height())
				elif attrib == "state_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_state = int(es.width())
					self.height_state = int(es.height())
				elif attrib == "tuner_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_tuner = int(es.width())
					self.height_tuner = int(es.height())
				elif attrib == "orbital_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_orbital = int(es.width())
					self.height_orbital = int(es.height())
				elif attrib == "eventeit_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width_eventeit = int(es.width())
					self.height_eventeit = int(es.height())
				elif attrib == "timericon_pos":
					x,y = value.split(",")
					self.timericon_pos_x = int(x)
					self.timericon_pos_y = int(y)
				elif attrib == "zapicon_pos":
					x,y = value.split(",")
					self.zapicon_pos_x = int(x)
					self.zapicon_pos_y = int(y)	
				elif attrib == "repeaticon_pos":
					x,y = value.split(",")
					self.repeaticon_pos_x = int(x)
					self.repeaticon_pos_y = int(y)
				elif attrib == "disabledicon_pos__with_icons":
					lst = value.split(";")
					ep = parsePosition(lst[0], ((1,1),(1,1)))
					self.disabledicon_pos_x = int(ep.x())	
					self.disabledicon_pos_y = int(ep.y())
					ep = parsePosition(lst[1], ((1,1),(1,1)))
					self.disabledicon_pos_x_icons = int(ep.x())
					self.disabledicon_pos_y_icons = int(ep.y())
				elif attrib == "recicon_pos":
					x,y = value.split(",")
					self.recicon_pos_x = int(x)
					self.recicon_pos_y = int(y)	
				elif attrib == "finishedicon_pos":
					x,y = value.split(",")
					self.finishedicon_pos_x = int(x)
					self.finishedicon_pos_y = int(y)
				elif attrib == "runningicon_pos":
					x,y = value.split(",")
					self.runningicon_pos_x = int(x)
					self.runningicon_pos_y = int(y)
				elif attrib == "timericon_size":
					es = parseSize(value, ((1,1),(1,1)))
					self.timericon_width = int(es.width())
					self.timericon_height = int(es.height())
				elif attrib == "zapicon_size":
					x,y = value.split(",")
					self.zapicon_width = int(x)
					self.zapicon_height = int(y)
				elif attrib == "repeaticon_size":
					x,y = value.split(",")
					self.repeaticon_width = int(x)
					self.repeaticon_height = int(y)	
				elif attrib == "disabledicon_size":
					x,y = value.split(",")
					self.disabledicon_width = int(x)
					self.disabledicon_height = int(y)
				elif attrib == "recicon_size":
					x,y = value.split(",")
					self.recicon_width = int(x)
					self.recicon_height = int(y)
				elif attrib == "finishedicon_size":
					x,y = value.split(",")
					self.finishedicon_width = int(x)
					self.finishedicon_height = int(y)
				elif attrib == "runningicon_size":
					x,y = value.split(",")
					self.runningicon_width = int(x)
					self.runningicon_height = int(y)
				elif attrib == "foregroundColorSelected":
					self.use_uniForegroundSelected = True
					attribs.append((attrib, value))
				else:
					attribs.append((attrib, value))
					
		self.skinAttributes = attribs
		return GUIComponent.applySkin(self, desktop, parent)
	
	
	def getFilterComponent(self,timer):
		if self.markPriorityTimers and len(pzyP4TfilterComponentList) > 0:
			if not pzyP4T_timerReminderAvailable:
				#patch for dreambox, important
				#RecordTimerEntry has no '.justremind'
				timer.justremind = timer.justplay
				
			ctr = 1
			for tpc,idx in pzyP4TfilterComponentList:
				if tpc.case_insensitive:
					tpcsearchString = tpc.searchString.lower()
					timer_name_lower = timer.name.lower()
				else:
					tpcsearchString = tpc.searchString
					timer_name_lower = timer.name
					
				timer_name_lower_ok = False
				if tpc.searchpart:
					if tpcsearchString in timer_name_lower :
						timer_name_lower_ok = True
				else:
					if tpcsearchString == timer_name_lower:
						timer_name_lower_ok = True
				
				if timer_name_lower_ok:
					if not tpc.use_servicename or tpc.service_ref_name == "" or tpc.service_ref_name == timer.service_ref.getServiceName():
						if (timer.justplay and tpc.justplay or timer.justremind and tpc.justremind) or (tpc.justremind and tpc.justremind and tpc.justrecord): #Spezialfall für Filter, alle .just* TRUE  and not timer.isRunning(): 
							ret = True
						else:
							ret = False
						return (tpc,ret,ctr)
				ctr +=1
				
		return (None,False,None)


	def tp_info(self, ref):
		if hasattr(ref, 'sref'):
			refstr = str(ref.sref)
		else:
			refstr = str(ref)	
		op = int(refstr.split(':', 10)[6][:-4] or "0",16)
		
		tun = None
		opos = None
		if '%3a//' in refstr:
			tun = "%s" % _("Stream")
			opos = ""
		elif op == 0xeeee:
			tun =  "%s" % _("DVB-T")
			opos = ""
		elif op == 0xffff:
			tun =  "%s" % _("DVB-C")
			opos = ""
		else:
			if op > 1800:
				op = 3600 - op
				direction = 'W'
			else:
				direction = 'E'
			tun =  "%s" % _("DVB-S")
			opos =  ("%d.%d\xc2\xb0%s") % (op // 10, op % 10, direction)
		return (tun,opos)
		
	
	def buildColorTimerEntry(self, timer, processed):
		#
		#  | <Service>                                   |
		#  | <Name of the Timer>        <eventeit>       |
		#  | <start, end> <P4T-Priority>        <state>  |
		#

		#tpc=pzyP4TFilterComponent() #test
		
		if not pzyP4T_timerReminderAvailable:
			#patch for dreambox, important
			#RecordTimerEntry has no '.justremind'
			timer.justremind = timer.justplay

		width = self.l.getItemSize().width()
		
		tpc,activate,prio = self.getFilterComponent(timer)
		if tpc: 
			if tpc.disabled or not activate:
				state = _("OFF")
			else:
				state = str(prio)

			pzyP4Ttext = " (P4T-%s)" %state
		else:
			pzyP4Ttext = ""

		if pzyP4TsettingsComponent.showIcons:
			x_serv = self.x_service_icons
			x_ev = self.x_event_icons
			x_evD = self.x_eventDesc_icons
			x_tim = self.x_time_icons
			x_st = self.x_state_icons
			x_tun = self.x_tuner_icons
			x_orb = self.x_orbital_icons
			x_eit = self.x_eventeit_icons
			y_serv = self.y_service_icons
			y_ev = self.y_event_icons
			y_evD = self.y_eventDesc_icons
			y_tim = self.y_time_icons
			y_st = self.y_state_icons
			y_tun = self.y_tuner_icons
			y_orb = self.y_orbital_icons
			y_eit = self.y_eventeit_icons
			
		else:
			x_serv = self.x_service
			x_ev = self.x_event
			x_evD = self.x_eventDesc
			x_tim = self.x_time
			x_st = self.x_state
			x_tun = self.x_tuner
			x_orb = self.x_orbital
			x_eit = self.x_eventeit
			y_serv = self.y_service
			y_ev = self.y_event
			y_evD = self.y_eventDesc
			y_tim = self.y_time
			y_st = self.y_state
			y_tun = self.y_tuner
			y_orb = self.y_orbital
			y_eit = self.y_eventeit
			
		if self.use_uniForegroundSelected:
			color_service_sel = None
			color_title_sel = None
			color_eventDesc_sel = None
			color_time_short_sel = None
			color_time_sel = None
			color_time_record_sel = None
			col_sel = None
			color_tuner_sel = None
			color_orbital_sel = None
			color_eventeit_sel = None
		else:
			color_service_sel = color_service_selected
			color_title_sel = color_title_selected
			color_eventDesc_sel = color_eventDesc_selected
			color_time_short_sel = color_time_short_selected
			color_time_sel = color_time_selected
			color_time_record_sel = color_time_record_selected
			color_tuner_sel = color_tuner_selected
			color_orbital_sel = color_orbital_selected
			color_eventeit_sel = color_eventeit_selected
			
		if pzyP4TsettingsComponent.showEventDesc:
			height_evD = 0
		else:
			height_evD = self.height_eventDesc
	
		
		timerdesc = str(timer.description).strip()
		if timerdesc == "":
			timerdesc = "-- No Description --"
			eventname = timer.name
		else:
			if pzyP4TsettingsComponent.showEventDesc:
				eventname = "%s > %s" %(timer.name, timer.description)
			else:
				eventname = timer.name
				
				
		res = [ None ]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_serv, y_serv, self.width_service, self.height_service, 0, self.service_align, timer.service_ref.getServiceName(),color_service,color_service_sel))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_ev, y_ev, self.width_event, self.height_event, 1, self.event_align, eventname, color_title, color_title_sel))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_evD, y_evD, self.width_eventDesc, height_evD, 4, self.eventDesc_align, timerdesc, color_eventDesc,color_eventDesc_sel))

		tun, opos = self.tp_info(timer.service_ref)
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tun, y_tun, self.width_tuner, self.height_tuner, 5, self.tuner_align, tun, color_tuner, color_tuner_sel))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_orb, y_orb, self.width_orbital, self.height_orbital, 6, self.orbital_align, opos, color_orbital, color_orbital_sel))
		
		repeatedtext = ""
		days = ( _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") )
		if timer.repeated:
			flags = timer.repeated
			count = 0
			for x in (0, 1, 2, 3, 4, 5, 6):
					if (flags & 1 == 1):
						if (count != 0):
							repeatedtext += ", "
						repeatedtext += days[x]
						count += 1
					flags = flags >> 1
			if timer.justplay or timer.justremind:
				if timer.end - timer.begin < 4: # rounding differences
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.begin)[1]))+ pzyP4Ttext, color_time_short, color_time_short_sel))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + ((" %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60)) + _("(ZAP)")+ _("(ZAP)") + pzyP4Ttext, color_time,color_time_sel))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60))+ pzyP4Ttext,color_time_record, color_time_record_sel))
			
			if pzyP4TsettingsComponent.showIcons:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.repeaticon_pos_x, self.repeaticon_pos_y, self.repeaticon_width, self.repeaticon_height, self.repeat_timer))
		else:
			if timer.justplay or timer.justremind:
				if timer.end - timer.begin < 4:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.begin))) + pzyP4Ttext, color_time_short, color_time_short_sel))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + _("(ZAP)") + pzyP4Ttext, color_time, color_time_sel))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x_tim, y_tim, self.width_time, self.height_time, 2, self.time_align, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + pzyP4Ttext,color_time_record, color_time_record_sel))
		
		bln_recicon = False
		bln_finishedicon = False
		bln_runningicon = False		
		if not processed:
			if timer.state == TimerEntry.StateWaiting:
				state = _("waiting")
				
				wait_long = (timer.begin - self.now) / 3600
				if wait_long >= 24:
					col = color_state_waiting_long
					col_auswahl = color_state_waiting_long_selected
					
					if pzyP4TsettingsComponent.showIcons:
						waiting_timer = self.waiting_timer_long
				else:
					col = color_state_waiting
					col_auswahl = color_state_waiting_selected
					
					if pzyP4TsettingsComponent.showIcons:
						waiting_timer = self.waiting_timer
						
			elif timer.state == TimerEntry.StatePrepared:
				state = _("about to start")
				col = color_state_starting
				col_auswahl = color_state_starting_selected
				
				bln_runningicon = True	
			elif timer.state == TimerEntry.StateRunning:
				if timer.justplay:
					state = _("zapped")
					col = color_state_running
					col_auswahl = color_state_running_selected
					
					bln_runningicon = True
				elif timer.justremind:
					state = _("Reminder")
					col = color_state_running
					col_auswahl = color_state_running_selected
					
					bln_runningicon = True
				else:
					state = _("recording...")
					col = color_state_recording
					col_auswahl = color_state_recording_selected
					
					bln_recicon = True
			elif timer.state == TimerEntry.StateEnded:
				state = _("done!")
				col = color_state_finished
				col_auswahl = color_state_finished_selected
				
				bln_finishedicon = True
			else:
				state = _("<unknown>")
				col = color_state_unknown
				col_auswahl = color_state_unknown_selected
				
		else:
			state = _("done!")
			col = color_state_finished
			col_auswahl = color_state_finished_selected
			
			bln_finishedicon = True

		if timer.disabled:
			state = _("disabled")
			png_timer = self.disabled_timer
			
			if timer.begin < self.now and timer.end > self.now:
				col = color_state_running
				col_auswahl = color_state_running_selected
				
			else:
				col = color_state_disabled
				col_auswahl = color_state_disabled_selected

		#if not pzyP4TsettingsComponent.use_uniForegroundSelected:
		if not self.use_uniForegroundSelected:
			col_sel = col_auswahl
			
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x_st, y_st, self.width_state, self.height_state, 3, self.state_align, state,col,col_sel))
		
		if timer.eit:
			eit = "eventID=" + str(timer.eit)
		else:
			eit = "keine eventID"
		
		if pzyP4TsettingsComponent.showEventEit:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x_eit, y_eit, self.width_eventeit, self.height_eventeit, 7, self.eventeit_align, eit,color_eventeit,color_eventeit_sel))
		
		if pzyP4TsettingsComponent.showIcons:
			if timer.state == TimerEntry.StateRunning:
				if (timer.dontSave or bln_recicon): 
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.recicon_pos_x, self.recicon_pos_y, self.recicon_width, self.recicon_height, self.instant_record))
				else:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.runningicon_pos_x, self.runningicon_pos_y, self.runningicon_width, self.runningicon_height, self.running_timer))
			else:
				if timer.disabled:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.disabledicon_pos_x_icons, self.disabledicon_pos_y_icons, self.disabledicon_width, self.disabledicon_height, self.disabled_timer))
				elif bln_finishedicon:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.finishedicon_pos_x, self.finishedicon_pos_y, self.finishedicon_width, self.finishedicon_height, self.finished_timer))
				elif bln_runningicon:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.runningicon_pos_x, self.runningicon_pos_y, self.runningicon_width, self.runningicon_height, self.running_timer))
				else:
					#waiting
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.timericon_pos_x, self.timericon_pos_y, self.timericon_width, self.timericon_height, waiting_timer))

			if timer.justplay or timer.justremind:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.zapicon_pos_x, self.zapicon_pos_y, self.zapicon_width, self.zapicon_height, self.zap_timer))

		else:
			if timer.disabled:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.disabledicon_pos_x, self.disabledicon_pos_y, self.timericon_width, self.timericon_height, self.disabled_timer))

		return res


###################################################################################################################################
###################################################################################################################################
###################################################################################################################################



class pzyP4TSettings:
	
	def __init__(self):
		
		#defaults
		
		self.filterComponentList = []

		self.use_skin_colors = False
		#self.use_uniForegroundSelected = True
		self.color_service = "#008B008B" #DarkMagenta
		self.color_service_selected = "#00FF00FF" #Magenta
		self.color_title = "#00FFFFFF" #White
		self.color_title_selected = "#00FFFF00" #Yellow
		self.color_eventDesc = "#00228B22" #ForestGreen
		self.color_eventDesc_selected = "#007CFC00" #Lawngreen
		self.color_time = "#00FFFFFF" #White
		self.color_time_selected = "#0000C8FF" #cy
		self.color_time_short = "#000066FF" #blue
		self.color_time_short_selected = "#000066FF" #blue
		self.color_time_record = "#00FFFFFF" #white
		self.color_time_record_selected = "#00FFFF00" #Yellow
		
		self.color_tuner = "#00FFFF66"   #or/ye
		self.color_tuner_selected = "#00FFFF66"   #or/ye
		self.color_orbital = "#00FFFF66"   #or/ye
		self.color_orbital_selected = "#00FFFF66"   #or/ye
		self.color_eventeit = "#00FFFF66"   #or/ye
		self.color_eventeit_selected = "#00FFFF66"   #or/ye
		
		self.color_state_waiting = "#00CD9B1D" #Darkgoldenrod3
		self.color_state_waiting_selected = "#00FFD700" #Gold
		self.color_state_waiting_long = "#001E90FF" #DodgerBlue
		self.color_state_waiting_long_selected = "#0000FFFF" #Blue4
		self.color_state_starting = "#00008B8B" #cyan4
		self.color_state_starting_selected = "#0000FFFF" #cyan
		self.color_state_running = "#00696969" #Dimgray
		self.color_state_running_selected = "#00D3D3D3" #Lightgray
		self.color_state_recording = "#00FF0000" #red
		self.color_state_recording_selected = "#00FF0000" #red
		self.color_state_finished = "#00228B22" #ForestGreen
		self.color_state_finished_selected = "#0000FA9A" #MediumSpringGree
		self.color_state_disabled = "#00FF6A6A" #Indianred
		self.color_state_disabled_selected = "#00FF6A6A" #Indianred
		self.color_state_unknown = "#004682B4" #Steelblue
		self.color_state_unknown_selected = "#0000F5FF" #turquoise1
		self.color_title_filter_disabled = "#00FF69B4" #HotPink
		
		self.showIcons = True
		self.showEventEit = False
		self.showEventDesc = False


	def setValues( self, \
	               filterComponentList, \
	               use_skin_colors, \
	               #use_uniForegroundSelected, \
	               color_service, \
	               color_service_selected, \
	               color_title, \
	               color_title_selected, \
	               color_eventDesc, \
	               color_eventDesc_selected, \
	               color_time, \
	               color_time_selected, \
	               color_time_short, \
	               color_time_short_selected, \
	               color_time_record, \
	               color_time_record_selected, \
	               color_tuner, \
	               color_tuner_selected, \
	               color_orbital, \
	               color_orbital_selected, \
	               color_eventeit, \
	               color_eventeit_selected, \
	               color_state_waiting, \
	               color_state_waiting_selected, \
	               color_state_waiting_long, \
	               color_state_waiting_long_selected, \
	               color_state_starting, \
	               color_state_starting_selected, \
	               color_state_running, \
	               color_state_running_selected, \
	               color_state_recording, \
	               color_state_recording_selected, \
	               color_state_finished, \
	               color_state_finished_selected, \
	               color_state_disabled, \
	               color_state_disabled_selected, \
	               color_state_unknown, \
	               color_state_unknown_selected, \
	               color_title_filter_disabled, \
	               showIcons, \
	               showEventEit, \
	               showEventDesc \
	               ):

		
		self.use_skin_colors = use_skin_colors
		#self.use_uniForegroundSelected = use_uniForegroundSelected
		
		self.color_service = color_service
		self.color_service_selected = color_service_selected
		self.color_title = color_title
		self.color_title_selected = color_title_selected
		self.color_eventDesc = color_eventDesc
		self.color_eventDesc_selected = color_eventDesc_selected
		self.color_time = color_time
		self.color_time_selected = color_time_selected
		self.color_time_short = color_time_short
		self.color_time_short_selected = color_time_short_selected
		
		self.color_time_record = color_time_record
		self.color_time_record_selected = color_time_record_selected
		
		self.color_tuner = color_tuner
		self.color_tuner_selected = color_tuner_selected
		self.color_orbital = color_orbital
		self.color_orbital_selected = color_orbital_selected
		self.color_eventeit = color_eventeit
		self.color_eventeit_selected = color_eventeit_selected
		
		self.color_state_waiting = color_state_waiting
		self.color_state_waiting_selected = color_state_waiting_selected
		self.color_state_waiting_long = color_state_waiting_long
		self.color_state_waiting_long_selected = color_state_waiting_long_selected
		self.color_state_starting = color_state_starting
		self.color_state_starting_selected = color_state_starting_selected
		
		self.color_state_running = color_state_running
		self.color_state_running_selected = color_state_running_selected
		self.color_state_recording = color_state_recording
		self.color_state_recording_selected = color_state_recording_selected
		self.color_state_finished = color_state_finished
		self.color_state_finished_selected = color_state_finished_selected
		
		self.color_state_disabled = color_state_disabled
		self.color_state_disabled_selected = color_state_disabled_selected
		self.color_state_unknown = color_state_unknown
		self.color_state_unknown_selected = color_state_unknown_selected
		self.color_title_filter_disabled = color_title_filter_disabled
		
		self.showIcons = showIcons
		self.showEventEit = showEventEit
		self.showEventDesc = showEventDesc
		
		
	def getClone(self, clone_fcl=False):
		s = pzyP4TSettings() #ok
		
		s.use_skin_colors = bool(self.use_skin_colors)
		#s.use_uniForegroundSelected = bool(self.use_uniForegroundSelected)
		s.color_title = str(self.color_title)
		s.color_title_selected = str(self.color_title_selected)
		s.color_title_filter_disabled = str(self.color_title_filter_disabled)
		s.color_eventDesc = str(self.color_eventDesc)
		s.color_eventDesc_selected = str(self.color_eventDesc_selected)
		s.color_service = str(self.color_service)
		s.color_service_selected = str(self.color_service_selected)
		s.color_time = str(self.color_time)
		s.color_time_selected = str(self.color_time_selected)
		s.color_time_short = str(self.color_time_short)
		s.color_time_short_selected = str(self.color_time_short_selected)
		s.color_time_record = str(self.color_time_record)
		s.color_time_record_selected = str(self.color_time_record_selected)

		s.color_tuner = str(self.color_tuner)
		s.color_tuner_selected = str(self.color_tuner_selected)
		s.color_orbital = str(self.color_orbital)
		s.color_orbital_selected = str(self.color_orbital_selected)
		s.color_eventeit = str(self.color_eventeit)
		s.color_eventeit_selected = str(self.color_eventeit_selected)
		
		s.color_state_disabled = str(self.color_state_disabled)
		s.color_state_disabled_selected = str(self.color_state_disabled_selected)
		s.color_state_waiting = str(self.color_state_waiting)
		s.color_state_waiting_selected = str(self.color_state_waiting_selected)
		s.color_state_waiting_long = str(self.color_state_waiting_long)
		s.color_state_waiting_long_selected = str(self.color_state_waiting_long_selected)
		s.color_state_starting = str(self.color_state_starting)
		s.color_state_starting_selected = str(self.color_state_starting_selected)
		s.color_state_running = str(self.color_state_running)
		s.color_state_running_selected = str(self.color_state_running_selected)
		s.color_state_recording = str(self.color_state_recording)
		s.color_state_recording_selected = str(self.color_state_recording_selected)
		s.color_state_finished = str(self.color_state_finished)
		s.color_state_finished_selected = str(self.color_state_finished_selected)
		s.color_state_unknown = str(self.color_state_unknown)
		s.color_state_unknown_selected = str(self.color_state_unknown_selected)

		s.showIcons = bool(self.showIcons)
		s.showEventEit = bool(self.showEventEit)
		s.showEventDesc = bool(self.showEventDesc)
		
		if clone_fcl:
			lst = []
			for e in self.filterComponentList:
				lst.append( e.getClone() )
			
			s.filterComponentList = lst
		
		return s
	
		
class pzyP4TFilterComponent:
	#(tpc,0) in pzyP4TFilterComponentList, 0 = new
	
	def __init__(self):
		self.disabled = False

		self.filterTitle = ""
		self.searchString = ""
		self.searchpart = True
		self.case_insensitive = True
		
		self.justremind = True
		self.justplay = True
		self.justrecord = True
		
		self.limitedTime = False
		self.filtertimeBegin = 0
		self.filtertimeEnd = 0
		
		self.use_servicename = False
		self.show_servicename = False
		
		self.service_ref = None
		self.service_ref_name = ""
	
		
	def getClone(self):
		tpc = pzyP4TFilterComponent() #ok
		
		tpc.disabled = bool(self.disabled)

		tpc.filterTitle = str(self.filterTitle)
		tpc.searchString = str(self.searchString)
		tpc.searchpart = bool(self.searchpart)
		tpc.case_insensitive = bool(self.case_insensitive)
		
		tpc.justremind = bool(self.justremind)
		tpc.justplay = bool(self.justplay)
		tpc.justrecord = bool(self.justrecord)
		
		tpc.use_servicename = bool(self.use_servicename)
		tpc.show_servicename = bool(self.show_servicename)
		
		tpc.service_ref = None
		tpc.service_ref_name = str(self.service_ref_name)
		
		return tpc
		
		
	def setValues( self, \
	               disabled = False, \
	               filterTitle = "", \
	               searchString = "", \
	               searchpart = True, \
	               case_insensitive = True, \
	               justremind = True, \
	               justplay = True, \
	               justrecord = True, \
	               limitedTime = False, \
	               filtertimeBegin = 0, \
	               filtertimeEnd = 0, \
	               use_servicename = False, \
	               service_ref = None, \
	               service_ref_name = "" \
	               ):
		
		self.disabled = disabled
		
		self.filterTitle = filterTitle
		self.searchString = searchString
		self.searchpart = searchpart
		self.case_insensitive = case_insensitive
		
		self.justremind = justremind
		self.justplay = justplay
		self.justrecord = justrecord
		
		self.limitedTime = limitedTime
		self.filtertimeBegin = filtertimeBegin
		self.filtertimeEnd = filtertimeEnd
		
		self.service_ref = use_servicename
		self.service_ref = service_ref
		self.service_ref_name = service_ref_name
	    
		
	def getValues(self):
		return (
		         self.disabled, \
		         self.filterTitle, \
		         self.searchString, \
		         self.searchpart, \
		         self.case_insensitive, \
		         self.justremind, \
		         self.justplay, \
		         self.justrecord, \
		         self.limitedTime, \
		         self.filtertimeBegin, \
		         self.filtertimeEnd, \
		         self.use_servicename, \
		         self.show_servicename, \
		         self.service_ref, \
		         self.service_ref_name \
		       )
	

	def __repr__(self):
		return " disabled: %s\n filterTitle: %s\n searchString: %s\n searchpart: %s\n case_insensitive: %s\n justremind: %s\n justplay: %s\n justrecord: %s\n limitedTime: %s\n filtertimeBegin: %s\n filtertimeEnd: %s\n use_servicename: %s\n show_servicename: %s\n service_ref: %s\n service_ref_name: %s\n\n"  \
		       %(
		          str(self.disabled), \
		          self.filterTitle, \
		          self.searchString, \
		          str(self.searchpart), \
		          str(self.case_insensitive), \
		          str(self.justremind), \
		          str(self.justplay), \
		          str(self.justrecord), \
		          str(self.limitedTime), \
		          FuzzyTime(self.filtertimeBegin), \
		          FuzzyTime(self.filtertimeEnd), \
		          #str(self.filtertimeBegin), \
		          #str(self.filtertimeEnd), \
		          str(self.use_servicename), \
		          str(self.show_servicename), \
			  str(self.service_ref), \
			  str(self.service_ref_name) \
		        )


###################################################################################################################################
###################################################################################################################################
###################################################################################################################################



class pzyP4TFilterList(Screen):

	def __init__(self,session):
		Screen.__init__(self,session)
		#self.skinName = ["pzyP4TFilterList","PluginBrowser"]
		
		self["red"] = Label(_("Remove"))
		self["green"] = Label(_("Save"))
		self["yellow"] = Label(_("Mode: Edit"))
		self["blue"] = Label(_("Sort: Priority"))
		
		self["Priority_Index"] = Label(_("Current Priority:"))
		self["FilterPriority"] = Label()
		
		self.filterdetails = FilterDetailList()
		self["Filter_Details"] = self.filterdetails
		
		self["KeyPressed"] = Button()
		self["KeyPressed"].hide()		
		
		self.autoTimer_importList = None
		
		self.filterlist = FilterList(list,True,eListboxPythonMultiContent)
		self.filterlist.onSelectionChanged.append(self.showFilterIndex)
		
		self["list"] = self.filterlist
		
		lst = []
		ctr = 1
		for el,idx in pzyP4TfilterComponentList: #(tpc,0)
			lst.append((el.getClone(),ctr))
		self.list = lst
		
		self.filterlist.list = self.list
		self.filterlist.l.setList(self.list)
		self.selectedElement = None
		
		self.sortedlist = []
		self.sortindex = 0

		self.togglemove = False
		self.toggleselected = False
		self.selected = -1
		
		self.kpa = Keypress2ascii([self.showPressedKey],[self.hidePressedKey])
		self.lastpressednumber = None
		
		self["actions"] = NumberActionMap(["PiPSetupActions","MenuActions","ColorActions","InfobarChannelSelection","ChannelSelectEPGActions","NumberActions"],  #ActionMap
		                            {       "1": self.keyNumberGlobal,
		                                    "2": self.keyNumberGlobal,
		                                    "3": self.keyNumberGlobal,
		                                    "4": self.keyNumberGlobal,
		                                    "5": self.keyNumberGlobal,
		                                    "6": self.keyNumberGlobal,
		                                    "7": self.keyNumberGlobal,
		                                    "8": self.keyNumberGlobal,
		                                    "9": self.keyNumberGlobal,
		                                    "0": self.keyNumberGlobal,
		                                    "red": self.removeFilter,
		                                    "green": self.saveFilters,
		                                    "yellow": self.toggle_movemode,
		                                    "blue": self.changeSortIndex, 
		                                    "up": self.menuListUp,
		                                    "down": self.menuListDown,
		                                    "left": self.menuListPageUp,
		                                    "right": self.menuListPageDown,
		                                    "menu": self.KeyMenu,
		                                    "cancel": self.Exit,
		                                    "ok": self.key_ok,
		                                    "historyNext": self.remove_filter_servicename,
		                                    "showEPGList": self.searchEPG,
		                                    "historyBack": self.importFromAutoTimer_helper,
		                                    #"size+": self.,
		                                    #"size-": self.
		                                    }, -1)

		self.setTitle("Timer Filter Arrangement")
		self.onExecBegin.append(self.first_start)


	def keyNumberGlobal(self, number):
		self.lastpressednumber = number
		self.kpa.pressed(number)


	def showPressedKey(self,data=None):
		if self.sortindex == 0:
			if self.lastpressednumber is None:
				return
			data = str(self.lastpressednumber * 10)
			
		if data is not None: 
			if data == " ":
				data = "SPACE"
			self["KeyPressed"].setText(data)
			self["KeyPressed"].show()
		
			
	def hidePressedKey(self,data=""):
		self["KeyPressed"].hide()
		
		if self.sortindex == 0:
			if self.lastpressednumber is None:
				return
			int_idx = self.lastpressednumber * 10 -1
			int_lastidx = len(self.filterlist.list)-1
			if int_idx < int_lastidx:
				self.filterlist.moveToIndex(int_idx)
			else:
				self.filterlist.moveToIndex(int_lastidx)
			self.lastpressednumber = None
			return

		elif self.sortindex == 1:
			lst=self.sortedlist

			ctr = 0		
			for el in lst:
				tpc,idx = el
				strel = str(tpc.filterTitle).strip()
					
				if strel.upper().startswith(data,0,1):
					self.filterlist.moveToIndex(ctr)
					break
				ctr +=1
			
			
	def getSorted(self,item): #(tpc,0)
		tpc,idx = item
		
		#tpc=pzyP4TFilterComponent() #test
		
		if self.sortindex == 1:
			if tpc.use_servicename:
				str_sref = tpc.service_ref_name
			else:
				str_sref = ""
			ritem = "%s %s" %(tpc.filterTitle.lower(), str_sref.lower() )
		else:
			ritem = idx
			
		return ritem
	
	
	def changeSortIndex(self,forceprio=False): 
		self.selectedElement = self.filterlist.getCurrent()
	
		if not self.selectedElement:
			return	
		
		if not forceprio and self.sortindex < 1: #add more options
			self.sortindex +=1 #title
		else:
			self.sortindex = 0 # prio

		if self.sortindex > 0 and self.sortindex < 2:
			text = _("Current Index:")
			mode = _("Sort: Title")
			self.sortedlist = sorted(self.list,key=self.getSorted)
		else:
			self.sortedlist = self.list
			text = _("Current Priority:")			
			mode = _("Sort: Priority")
			
		self.filterlist.l.setList(self.sortedlist)	
		self.filterlist.moveToIndex(self.sortedlist.index(self.selectedElement))
		self["Priority_Index"].setText(text)	
		self["blue"].setText(mode)
		
		
	def filterListStartPos(self):
		self.filterlist.moveToIndex(0)
		

	def KeyMenu(self):
		self.session.openWithCallback(
			self.menuCallback,
			cbx,
		        title = "Menu",
			list = [ 
		                (_("Edit/Move Filter Toggle"), self.toggle_movemode),
		                (_("Sort Priority/Title Toggle"), self.changeSortIndex),
		                (_("Edit Filter"), self.open_filter_edit),
		                (_("Remove Filter"), self.removeFilter),
		                (_("Remove Servicename From Filter"), self.remove_filter_servicename),
		                (_("Search EPG: Similar Events"), self.searchEPG),
		                (_("Import From AutoTimer"), self.importFromAutoTimer_helper),
		                (_("Save & Exit Editor"), self.saveFilters),
		                
		        ],
		        keys = [ "yellow", "blue", "ok", "red", ">", "info", "<", "green" ]
		)

		
	def first_start(self):
		self["list"].moveToIndex(0)
		self.showFilterIndex()
		
		
	def showFilterIndex(self):
		prio = ""
		tpc = self.filterlist.getCurrent()
		if tpc:
			idx = self.filterlist.getSelectionIndex()
			prio = str(idx + 1)
		else:
			prio = ""
			
		self.filterdetails.setDetailList(tpc)
		self["FilterPriority"].setText(prio)
		
		
	def open_filter_edit(self):
		#tpc = pzyP4TFilterComponent() #test
		
		self.selectedElement = self.filterlist.getCurrent()
		if self.selectedElement:
			tpc = self.selectedElement		
			self.session.openWithCallback(
				self.__back_PzyP4TFilterEditor,
				PzyP4TFilterEditor,
				cur_filterComponent=tpc
			)		
		
		
	def __back_PzyP4TFilterEditor(self,tpc=None):
		pass
		

	def importFromAutoTimer_helper(self):
		if not pzyP4T_AutoTimerAvailable:
			return
		
		self.session.openWithCallback(
	                self.menuCallback,
	                cbx,
		        title = "Import From AutoTimer",
	                list = [
	                        (_("Import Single Event"), self.importFromAutoTimer),
	                        (_("Import All Events"), self.importAllFromAutoTimer),
	                ]
	        )

		
	def menuCallback(self, ret):
		ret and ret[1]()
		
		
	def read_autoTimerXML(self):
		removeInstance = False
		try:
			from Plugins.Extensions.AutoTimer.plugin import autotimer

			if autotimer is None:
				removeInstance = True
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()

			autotimer.readXml()
		except Exception as e:
			self.session.open(
				MessageBox,
				_("Could not read AutoTimer timer list: %s") % e,
				type = MessageBox.TYPE_ERROR
			)
		else:
			options = [(x.match, x.match) for x in autotimer.getTimerList()]
			
			self.autoTimer_importList = options
	
		finally:
			if removeInstance:
				autotimer = None
				
		
	def importFromAutoTimer(self,all_entries=False):
		if not self.autoTimer_importList:
			self.read_autoTimerXML()
		
		self.changeSortIndex(True)
		
		if not all_entries:
			self.session.openWithCallback(
		                self.__back_importFromAutoTimer,
		                cbx,
		                title = _("Select Text To Search For"),
		                list = sorted(self.autoTimer_importList,key=lambda x: x[0].lower())
		)
		else:
			lst = []
			lst_filters = self["list"].list
			for data,title in self.autoTimer_importList:
				bln_found = False
				for f,idx in lst_filters:
					if f.case_insensitive:
						tpcsearchString = f.searchString.lower()
					else:
						tpcsearchString = f.searchString
					
					if title.lower() == tpcsearchString:
						bln_found = True
						break

				if not bln_found:
					tpc = pzyP4TFilterComponent()
					
					tpc.disabled = False
					tpc.filterTitle = title
					tpc.searchString = title
					tpc.searchpart = True
					tpc.case_insensitive = True
					tpc.use_servicename = False
					tpc.show_servicename = False
					tpc.justremind = True
					tpc.justplay = True
					tpc.justrecord = False
					
					# add more options
					
					lst.append((tpc,0))
			
			self["list"].list.extend(lst)
			
				
		
	def importAllFromAutoTimer(self):
		self.importFromAutoTimer(True)
				
				
	def __back_importFromAutoTimer(self,data):
		#single entry!!
		if data and data[1]:
		
			title = data[1]
			
			tpc = pzyP4TFilterComponent()
			
			tpc.disabled = False
			tpc.filterTitle = title
			tpc.searchString = title
			tpc.searchpart = True
			tpc.case_insensitive = True
			tpc.use_servicename = False
			tpc.show_servicename = False
			tpc.justremind = True
			tpc.justplay = True
			tpc.justrecord = False
			
			# add more options
			
			lst_filters = self["list"]
			
			lst_filters.list.append((tpc,0))
			lst_filters.l.setList(lst_filters.list)
			self.showFilterIndex()
			
		
	def searchEPG(self, searchString = None, searchSave = True):
		if not pzyP4T_EPGSearchAvailable:
			return
		
		#similar timers
		cur = self.filterlist.getCurrent()
		if cur and cur[0]:
			tpc = cur[0]
			self.session.openWithCallback(
		                self.__EPGSearch_callback,
		                EPGSearch, 
		                tpc.searchString
		        )	
			
	def __EPGSearch_callback(self,data=None):
		self.showFilterIndex()
	
		
	def saveFilters(self):
		global pzyP4TsettingsComponent
		global pzyP4TfilterComponentList
		global pzyP4T_writeSettings

		self.changeSortIndex(True)
		
		pzyP4TfilterComponentList = self.filterlist.list[:]
		pzyP4TsettingsComponent.filterComponentList = pzyP4TfilterComponentList
		self.filterlist.list = None
		
		pzyP4T_writeSettings = True
		self.close()
	
	
	def Exit(self):
		self.autoTimer_importList = None
		self.close()
		
			
	def toggle_movemode(self):
		if not len(self.list) > 0:
			return
		
		self.togglemove = not self.togglemove
		
		if self.togglemove:
			mode = "Mode: %s" %(_("Move"))
		else:
			mode = "Mode: %s" %(_("Edit"))
			self.toggleselected = False
			self.selected = -1
		
		self["yellow"].setText(mode)
		
		
	def key_ok(self):
		if not len(self.list) > 0:
			return		
		
		if self.togglemove:
			self.toggleselected = not self.toggleselected
			
			#movemode
			if self.toggleselected:
				self.selected = self.filterlist.getSelectedIndex()
				selectstate = "--- %s" % _("Filter Selected")   
			else:
				self.selected = -1
				selectstate = ""
					
			self.setTitle("%s --- %s %s" %(PZYP4T_VERSION, _("Filter Arrangement"),selectstate))

		else:
			#editmode
			self.open_filter_edit()
			
			
	def doMove(self, func):
		cur = self.filterlist.getCurrent()
		if not cur:
			return
		
		if self.selected != -1:
			if self.sortindex != 0:
				self.changeSortIndex(True)
			
			oldpos = self.filterlist.getSelectedIndex()
			func()
			entry = self.list.pop(oldpos)
			newpos = self.filterlist.getSelectedIndex()
			self.list.insert(newpos, entry)
			self.filterlist.l.setList(self.list)
		else:
			func()
		
		
	def menuListPageUp(self):
		self.doMove(self.filterlist.pageUp)

		
	def menuListPageDown(self):
		self.doMove(self.filterlist.pageDown)


	def menuListUp(self):
		self.doMove(self.filterlist.up)


	def menuListDown(self):
		self.doMove(self.filterlist.down)

	
	def removeFilter(self):
		if len(self.list) > 0:
			cur = self.filterlist.getCurrent()
			self.list.pop(self.list.index(cur))
			
			if self.sortindex > 0 and self.sortindex < 2:
				self.sortedlist = sorted(self.list,key=self.getSorted)
			else:
				self.sortedlist = self.list			
			self.filterlist.l.setList(self.sortedlist)
			
			
	def remove_filter_servicename(self):
		cur = self.filterlist.getCurrent()
		if cur and cur[0]:		
			tpc = cur[0]
			tpc.use_servicename = False
			tpc.show_servicename = False
			
			if self.sortindex > 0 and self.sortindex < 2:
				sortedlist = self.sortedlist
			else:
				sortedlist = self.list			
			self.filterlist.l.setList(sortedlist)
	

			
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################



class FilterList(MenuList):

	def __init__(self, filters, enableWrapAround=True, content=eListboxPythonMultiContent):
		MenuList.__init__(self, list, enableWrapAround, content)

		self.use_uniForegroundSelected  = False
		
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 24))
		self.l.setItemHeight(25)
		self.l.setBuildFunc(self.buildColorEntry)
		self.list=filters
		
		
	def applySkin(self,desktop,parent):
		global color_title_filter_disabled
		global width_service
		
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font_0":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "font_1":
					self.l.setFont(1, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "color_title_filter_disabled":
					color_title_filter_disabled = parseColor(value).argb()
				elif attrib == "width_service":
					width_service = int(value)
				elif attrib == "foregroundColorSelected":
					self.use_uniForegroundSelected = True
					attribs.append((attrib, value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self,desktop,parent)
	
	
	def buildColorEntry(self,filterComponent,x):
		width = self.l.getItemSize().width()
		height = self.l.getItemSize().height()
		
		if filterComponent.disabled:
			col_t = color_title_filter_disabled
			col_s = color_title_filter_disabled
		else:
			col_t = color_title
			if filterComponent.use_servicename:
				col_s = color_service
			else:
				col_s = color_title_filter_disabled
				
				
		#if pzyP4TsettingsComponent.use_uniForegroundSelected:
		if self.use_uniForegroundSelected:
			col_t_sel = None
			col_s_sel = None
		else:
			col_t_sel = col_t
			col_s_sel = col_s			
				
		menuEntry = [(filterComponent)]
		menuEntry.append(MultiContentEntryText(pos=(0, 0), size=(width-width_service, height), font=0, flags=RT_VALIGN_CENTER, text=filterComponent.filterTitle,color=col_t ,color_sel=col_t_sel))
		if filterComponent.use_servicename or not filterComponent.use_servicename and filterComponent.show_servicename:
			menuEntry.append(MultiContentEntryText(pos=(width-width_service, 0), size=(width_service,height), font=1, flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=filterComponent.service_ref_name,color=col_s ,color_sel=col_s_sel))
		
		return menuEntry

	
	def getCurrent(self):
		return self.l.getCurrentSelection()

	
	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x[0] == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

			
			
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
			

class FilterDetailList(MenuList):

	def __init__(self, list=[], enableWrapAround=True, content=eListboxPythonMultiContent):
		MenuList.__init__(self, list, enableWrapAround, content)

		self.l.setFont(0, gFont("Regular", 16))
		self.l.setItemHeight(25)
		self.l.setBuildFunc(self.buildEntry)
		self.list=list
	
		
	def applySkin(self,desktop,parent):
		global color_title_filter_disabled
		
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self,desktop,parent)

	
	def setDetailList(self,filterComponent): #(tpc,0)
		if filterComponent:
					
			tpc = filterComponent[0]
	
			lst = []
			lst.append((tpc.searchString,None))
			
			if tpc.searchpart:
				searchparttext = "Partial Search"
			else:
				searchparttext = "Full Search"
			lst.append((searchparttext,None))
			
			if tpc.case_insensitive:
				case_insensitivetext = "Case Insensitive"
			else:
				case_insensitivetext = "Case Sensitive"
			lst.append((case_insensitivetext,0))
			
			if tpc.justremind and tpc.justplay and tpc.justrecord:
				filterTypetext = "Reminder, Zap, Recordings"
			elif tpc.justremind and tpc.justplay:
				filterTypetext = "Reminder, Zap"			
			elif not tpc.justremind and not tpc.justplay:
				filterTypetext = "Recordings"
			elif tpc.justremind and not tpc.justplay:
				filterTypetext = "Reminder"
			elif tpc.justplay and not tpc.justremind:
				filterTypetext = "Zap"			
			lst.append((filterTypetext,None))
			
			if tpc.use_servicename:
				use_servicenametext = "Only For Service:  [%s]" %(tpc.service_ref_name)
			else:
				use_servicenametext = "All Services"
			lst.append((use_servicenametext,None))
			
			if tpc.show_servicename:
				show_servicenametext = "Show Servicename Always"
			else:
				show_servicenametext = "Show Active Servicename"
			lst.append((show_servicenametext,None))
		else:
			lst = []
		self.list = lst
		self.l.setList(self.list)
		
	
	def buildEntry(self,detailtext,x):
		width = self.l.getItemSize().width()
		height = self.l.getItemSize().height()
				
		menuEntry = [(None)]
		menuEntry.append(MultiContentEntryText(pos=(0, 0), size=(width, height), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=detailtext))
		return menuEntry

	
	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur

	
	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x[0] == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

			
			
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
			
			
			
class PzyP4TChannelSelection(SimpleChannelSelection):
	def __init__(self, session, timer=None):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = ["PzyP4TChannelSelection","SimpleChannelSelection"]

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.open(
				PzyP4TEPGSelection,
				ref
			)    

			
class PzyP4TEPGSelection(EPGSelection):
	def __init__(self, *args):
		EPGSelection.__init__(self, *args)
		self.skinName = ["PzyP4TEPGSelection", "EPGSelection"]
		self["VKeyIcon"] = Pixmap()
		
		
	def infoKeyPressed(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		tpc = pzyP4TFilterComponent()
		tpc.disabled=False
		tpc.filterTitle = evt and evt.getEventName() or ""
		tpc.searchString = tpc.filterTitle
		tpc.searchpart = True
		tpc.case_insensitive = True
		tpc.justremind = True
		tpc.justplay = True
		tpc.justrecord = True
		tpc.use_servicename = True
		tpc.show_servicename = False
		tpc.service_ref_name = sref.getServiceName()
		
		self.open_PzyP4TFilterEditor((tpc,0))
		
		
	def open_PzyP4TFilterEditor(self,filterComponent=None):
			self.session.openWithCallback(
				self.__back_open_PzyP4TFilterEditor,
				PzyP4TFilterEditor,
				cur_filterComponent=filterComponent
			)			
			
			
	def __back_open_PzyP4TFilterEditor(self,filterComponent=None):
		global pzyP4T_writeSettings
		
		if filterComponent:
			pzyP4TfilterComponentList.append((filterComponent,0))
			pzyP4T_writeSettings = True
	
	
	def KeyText(self):
		self.infoKeyPressed()



###################################################################################################################################
###################################################################################################################################
###################################################################################################################################



class PzyP4TSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		global pzyP4TsettingsComponent
		
		Screen.__init__(self, session)
		self.skinName = ["PzyP4TSetup","TimerEntry"]
		
		self.session = session
				
		self.onClose.append(self.abort)
		self.configList = None

		self.onLayoutFinish.append(self.firstStart)
		
		self.config = ConfigList([],session)
		self["config"] = self.config 
		
		self["VKeyIcon"] = Pixmap()
		
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()		
		
		self.color_preview = Label(_("This Is Your Current Color"))
		self["color_preview"] = self.color_preview
		
		#s=pzyP4TSettings() #test
		
		s = pzyP4TsettingsComponent.getClone()
		
		self.showIcons = NoSave(ConfigSelection(default=str(s.showIcons), choices=[("True","yes"), ("False","no")]))
		self.showEventEit = NoSave(ConfigSelection(default=str(s.showEventEit), choices=[("True","yes"), ("False","no")]))
		self.use_skin_colors = NoSave(ConfigSelection(default=str(s.use_skin_colors), choices=[("True","yes"), ("False","no")]))
		self.showEventDesc = NoSave(ConfigSelection(default=str(s.showEventDesc), choices=[("True","yes"), ("False","no")]))
		
		#self.use_uniForegroundSelected = NoSave(ConfigSelection(default=str(s.use_uniForegroundSelected), choices=[("True","yes"), ("False","no")]))
		self.color_title = NoSave(ConfigText(default=str(s.color_title), fixed_size=False, visible_width=40))
		self.color_title_selected = NoSave(ConfigText(default=str(s.color_title_selected), fixed_size=False, visible_width=40))
		self.color_eventDesc = NoSave(ConfigText(default=str(s.color_eventDesc), fixed_size=False, visible_width=40))
		self.color_eventDesc_selected = NoSave(ConfigText(default=str(s.color_eventDesc_selected), fixed_size=False, visible_width=40))
		self.color_service = NoSave(ConfigText(default=str(s.color_service), fixed_size=False, visible_width=40))
		self.color_service_selected = NoSave(ConfigText(default=str(s.color_service_selected), fixed_size=False, visible_width=40))
		self.color_time = NoSave(ConfigText(default=str(s.color_time), fixed_size=False, visible_width=40))
		self.color_time_selected = NoSave(ConfigText(default=str(s.color_time_selected), fixed_size=False, visible_width=40))
		self.color_time_short = NoSave(ConfigText(default=str(s.color_time_short), fixed_size=False, visible_width=40))
		self.color_time_short_selected = NoSave(ConfigText(default=str(s.color_time_short_selected), fixed_size=False, visible_width=40))
		self.color_time_record = NoSave(ConfigText(default=str(s.color_time_record), fixed_size=False, visible_width=40))
		self.color_time_record_selected = NoSave(ConfigText(default=str(s.color_time_record_selected), fixed_size=False, visible_width=40))
		
		self.color_tuner = NoSave(ConfigText(default=str(s.color_tuner), fixed_size=False, visible_width=40))
		self.color_tuner_selected = NoSave(ConfigText(default=str(s.color_tuner_selected), fixed_size=False, visible_width=40))
		self.color_orbital = NoSave(ConfigText(default=str(s.color_orbital), fixed_size=False, visible_width=40))
		self.color_orbital_selected = NoSave(ConfigText(default=str(s.color_orbital_selected), fixed_size=False, visible_width=40))
		
		self.color_eventeit = NoSave(ConfigText(default=str(s.color_eventeit), fixed_size=False, visible_width=40))
		self.color_eventeit_selected = NoSave(ConfigText(default=str(s.color_eventeit_selected), fixed_size=False, visible_width=40))
		
		self.color_state_waiting = NoSave(ConfigText(default=str(s.color_state_waiting), fixed_size=False, visible_width=40))
		self.color_state_waiting_selected = NoSave(ConfigText(default=str(s.color_state_waiting_selected), fixed_size=False, visible_width=40))
		self.color_state_waiting_long = NoSave(ConfigText(default=str(s.color_state_waiting_long), fixed_size=False, visible_width=40))
		self.color_state_waiting_long_selected = NoSave(ConfigText(default=str(s.color_state_waiting_long_selected), fixed_size=False, visible_width=40))
		self.color_state_starting = NoSave(ConfigText(default=str(s.color_state_starting), fixed_size=False, visible_width=40))
		self.color_state_starting_selected = NoSave(ConfigText(default=str(s.color_state_starting_selected), fixed_size=False, visible_width=40))
		self.color_state_running = NoSave(ConfigText(default=str(s.color_state_running), fixed_size=False, visible_width=40))
		self.color_state_running_selected = NoSave(ConfigText(default=str(s.color_state_running_selected), fixed_size=False, visible_width=40))
		self.color_state_recording = NoSave(ConfigText(default=str(s.color_state_recording), fixed_size=False, visible_width=40))
		self.color_state_recording_selected = NoSave(ConfigText(default=str(s.color_state_recording_selected), fixed_size=False, visible_width=40))
		self.color_state_finished = NoSave(ConfigText(default=str(s.color_state_finished), fixed_size=False, visible_width=40))
		self.color_state_finished_selected = NoSave(ConfigText(default=str(s.color_state_finished_selected), fixed_size=False, visible_width=40))
		self.color_state_disabled = NoSave(ConfigText(default=str(s.color_state_disabled), fixed_size=False, visible_width=40))
		self.color_state_disabled_selected = NoSave(ConfigText(default=str(s.color_state_disabled_selected), fixed_size=False, visible_width=40))
		self.color_state_unknown = NoSave(ConfigText(default=str(s.color_state_unknown), fixed_size=False, visible_width=40))
		self.color_state_unknown_selected = NoSave(ConfigText(default=str(s.color_state_unknown_selected), fixed_size=False, visible_width=40))
		self.color_title_filter_disabled = NoSave(ConfigText(default=str(s.color_title_filter_disabled), fixed_size=False, visible_width=40))


		self["actions"] = NumberActionMap(["ColorActions","SetupActions","VirtualKeyboardActions","ChannelSelectEPGActions"],
		                            {       "green": self.save_Configuration,
		                                    "cancel": self.Exit,
		                                    "red": self.Exit,
		                                    #"blue": self.
		                                    "showEPGList": self.key_Info,
		                                    "1": self.keyNumberGlobal,
		                                    "2": self.keyNumberGlobal,
		                                    "3": self.keyNumberGlobal,
		                                    "4": self.keyNumberGlobal,
		                                    "5": self.keyNumberGlobal,
		                                    "6": self.keyNumberGlobal,
		                                    "7": self.keyNumberGlobal,
		                                    "8": self.keyNumberGlobal,
		                                    "9": self.keyNumberGlobal,
		                                    "0": self.keyNumberGlobal,
		                                    "ok": self.key_ok
		                                    }, 0)

		self.setTitle("Timer Setup" + " -- " + PZYP4T_VERSION )

		self.configList = self.fillConfigList()
		ConfigListScreen.__init__(self, self.configList)

		#########################################################################

	def firstStart(self):
		self["config"].onSelectionChanged.append(self.set_colorpreview)
		self.set_colorpreview()
		

	def key_ok(self):
		self.KeyText()
		
		
	def KeyText(self):
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title = self["config"].getCurrent()[0], text = self["config"].getCurrent()[1].getValue())

		
	def VirtualKeyBoardCallback(self, callback = None):
		ConfigListScreen.VirtualKeyBoardCallback(self,callback)
		self.set_colorpreview()
		

	def key_Info(self):
		self.set_colorpreview()
		

	def set_colorpreview(self):
		val = self["config"].getCurrent()[1].getValue()
		if not val:
			return
		
		grgb = pzyparseColor(val)	
		if grgb: #gRGB
			self.color_preview.instance.setForegroundColor(grgb)
			self["config"].instance.setForegroundColorSelected(grgb)
		

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)


	def keyRight(self):
		ConfigListScreen.keyRight(self)


	def keyNumberGlobal(self, number):
		self.KeyText()
		

	def keyGotAscii(self):
		self.KeyText()
	
	#########################################################################

	def fillConfigList(self):
		list = []
		
		list.append(getConfigListEntry(_("Show Icons") + ":", self.showIcons))
		list.append(getConfigListEntry(_("Show EventEit") + ":", self.showEventEit))
		list.append(getConfigListEntry(_("Use Skin-Colors") + ":", self.use_skin_colors))
		list.append(getConfigListEntry(_("Show Extended Eventname") + ":", self.showEventDesc))
		#list.append(getConfigListEntry(_("Unique 'ForegroundSelected'") + ":", self.use_uniForegroundSelected))
		list.append(getConfigListEntry(_("Eventname") + ":", self.color_title))
		list.append(getConfigListEntry(_("Eventname Selected") + ":", self.color_title_selected))
		list.append(getConfigListEntry(_("Eventdescription") + ":", self.color_eventDesc))
		list.append(getConfigListEntry(_("Eventdescription Selected") + ":", self.color_eventDesc_selected))
		list.append(getConfigListEntry(_("Servicename") + ":", self.color_service))
		list.append(getConfigListEntry(_("Servicename Selected") + ":", self.color_service_selected))
		list.append(getConfigListEntry(_("Time - With Endtime") + ":", self.color_time))
		list.append(getConfigListEntry(_("Time - With Endtime Selected") + ":", self.color_time_selected))
		list.append(getConfigListEntry(_("Time - Without Endtime") + ":", self.color_time_short))
		list.append(getConfigListEntry(_("Time - Without Endtime Selected") + ":", self.color_time_short_selected))
		list.append(getConfigListEntry(_("Time - Of Recordings") + ":", self.color_time_record))
		list.append(getConfigListEntry(_("Time - Of Recordings Selected") + ":", self.color_time_record_selected))
		
		list.append(getConfigListEntry(_("Tuner") + ":", self.color_tuner))
		list.append(getConfigListEntry(_("Tuner Selected") + ":", self.color_tuner_selected))
		list.append(getConfigListEntry(_("Orbital Position") + ":", self.color_orbital))
		list.append(getConfigListEntry(_("Orbital Position Selected") + ":", self.color_orbital_selected))
		
		list.append(getConfigListEntry(_("Event ID") + ":", self.color_eventeit))
		list.append(getConfigListEntry(_("Event ID Selected") + ":", self.color_eventeit_selected))
		
		list.append(getConfigListEntry(_("State - Waiting") + ":", self.color_state_waiting))
		list.append(getConfigListEntry(_("State - Waiting Selected") + ":", self.color_state_waiting_selected))
		list.append(getConfigListEntry(_("State - Waiting Long") + ":", self.color_state_waiting_long))
		list.append(getConfigListEntry(_("State - Waiting Long Selected") + ":", self.color_state_waiting_long_selected))
		list.append(getConfigListEntry(_("State - Starting") + ":", self.color_state_starting))
		list.append(getConfigListEntry(_("State - Starting Selected") + ":", self.color_state_starting_selected))
		list.append(getConfigListEntry(_("State - Running") + ":", self.color_state_running))
		list.append(getConfigListEntry(_("State - Running Selected") + ":", self.color_state_running_selected))
		list.append(getConfigListEntry(_("State - Recording") + ":", self.color_state_recording))
		list.append(getConfigListEntry(_("State - Recording Selected") + ":", self.color_state_recording_selected))
		list.append(getConfigListEntry(_("State - Finished") + ":", self.color_state_finished))
		list.append(getConfigListEntry(_("State - Finished Selected") + ":", self.color_state_finished_selected))
		list.append(getConfigListEntry(_("State - Disabled") + ":", self.color_state_disabled))
		list.append(getConfigListEntry(_("State - Disabled Selected") + ":", self.color_state_disabled_selected))
		list.append(getConfigListEntry(_("State - Unknown") + ":", self.color_state_unknown))
		list.append(getConfigListEntry(_("State - Unknown Selected") + ":", self.color_state_unknown_selected))
		
		list.append(getConfigListEntry(_("Filter Disabled (Filterlist)") + ":", self.color_title_filter_disabled))
	
		return list


	def save_Configuration(self):
		global color_title
		global color_title_selected
		global color_title_filter_disabled
		global color_eventDesc
		global color_eventDesc_selected
		global color_service
		global color_service_selected
		global color_time
		global color_time_selected
		global color_time_short
		global color_time_short_selected
		global color_time_record
		global color_time_record_selected
		
		global color_tuner
		global color_tuner_selected
		global color_orbital
		global color_orbital_selected
		
		global color_eventeit
		global color_eventeit_selected
		
		global color_state_waiting
		global color_state_waiting_selected
		global color_state_waiting_long
		global color_state_waiting_long_selected
		global color_state_starting
		global color_state_starting_selected
		global color_state_running
		global color_state_running_selected
		global color_state_recording
		global color_state_recording_selected
		global color_state_finished
		global color_state_finished_selected
		global color_state_disabled
		global color_state_disabled_selected
		global color_state_unknown
		global color_state_unknown_selected
		global pzyP4T_writeSettings
		global pzyP4TsettingsComponent

		
		if self["config"].isChanged():
			pzyP4T_writeSettings = True

		#s = pzyP4TSettings() #test
		
		s = pzyP4TsettingsComponent #ok
		
		s.showIcons = eval(self.showIcons.value)
		s.showEventEit = eval(self.showEventEit.value)
		
		s.showEventDesc = eval(self.showEventDesc.value)
		
		s.use_skin_colors = eval(self.use_skin_colors.value)
		#s.use_uniForegroundSelected = eval(self.use_uniForegroundSelected.value)
		
		s.color_title = str(self.color_title.value)
		s.color_title_selected = str(self.color_title_selected.value)
		s.color_eventDesc = str(self.color_eventDesc.value)
		s.color_eventDesc_selected = str(self.color_eventDesc_selected.value)
		s.color_service = str(self.color_service.value) 
		s.color_service_selected = str(self.color_service_selected.value)
		s.color_time = str(self.color_time.value)
		s.color_time_selected = str(self.color_time_selected.value)
		s.color_time_short = str(self.color_time_short.value)
		s.color_time_short_selected = str(self.color_time_short_selected.value)
		s.color_time_record = str(self.color_time_record.value)
		s.color_time_record_selected = str(self.color_time_record_selected.value)
		
		s.color_tuner = str(self.color_tuner.value)
		s.color_tuner_selected = str(self.color_tuner_selected.value)
		s.color_orbital = str(self.color_orbital.value)
		s.color_orbital_selected = str(self.color_orbital_selected.value)
		
		s.color_eventeit = str(self.color_eventeit.value)
		s.color_eventeit_selected = str(self.color_eventeit_selected.value)
		
		s.color_state_waiting = str(self.color_state_waiting.value)
		s.color_state_waiting_selected = str(self.color_state_waiting_selected.value)
		s.color_state_waiting_long = str(self.color_state_waiting_long.value)
		s.color_state_waiting_long_selected = str(self.color_state_waiting_long_selected.value)
		s.color_state_starting = str(self.color_state_starting.value) 
		s.color_state_starting_selected = str(self.color_state_starting_selected.value)
		s.color_state_running = str(self.color_state_running.value)
		s.color_state_running_selected = str(self.color_state_running_selected.value)
		s.color_state_recording = str(self.color_state_recording.value) 
		s.color_state_recording_selected = str(self.color_state_recording_selected.value)
		s.color_state_finished = str(self.color_state_finished.value) 
		s.color_state_finished_selected = str(self.color_state_finished_selected.value)
		s.color_state_disabled = str(self.color_state_disabled.value) 
		s.color_state_disabled_selected = str(self.color_state_disabled_selected.value)
		s.color_state_unknown = str(self.color_state_unknown.value)
		s.color_state_unknown_selected = str(self.color_state_unknown_selected.value)
		s.color_title_filter_disabled = str(self.color_title_filter_disabled.value)
		

		#Apply Colors
		if not s.use_skin_colors:
			color_title = e2color2hex(s.color_title)
			color_title_selected = e2color2hex(s.color_title_selected)
			color_eventDesc = e2color2hex(s.color_eventDesc) 
			color_eventDesc_selected = e2color2hex(s.color_eventDesc_selected)
			color_service = e2color2hex(s.color_service) 
			color_service_selected = e2color2hex(s.color_service_selected)
			color_time = e2color2hex(s.color_time) 
			color_time_selected = e2color2hex(s.color_time_selected) 
			color_time_short = e2color2hex(s.color_time_short) 
			color_time_short_selected = e2color2hex(s.color_time_short_selected) 
			color_time_record = e2color2hex(s.color_time_record) 
			color_time_record_selected = e2color2hex(s.color_time_record_selected)
			
			color_tuner = e2color2hex(s.color_tuner)
			color_tuner_selected = e2color2hex(s.color_tuner_selected)
			color_orbital = e2color2hex(s.color_orbital)
			color_orbital_selected = e2color2hex(s.color_orbital_selected)
			
			color_eventeit = e2color2hex(s.color_eventeit)
			color_eventeit_selected = e2color2hex(s.color_eventeit_selected)
			
			color_state_waiting = e2color2hex(s.color_state_waiting) 
			color_state_waiting_selected = e2color2hex(s.color_state_waiting_selected)
			color_state_waiting_long = e2color2hex(s.color_state_waiting_long)
			color_state_waiting_long_selected = e2color2hex(s.color_state_waiting_long_selected)
			color_state_starting = e2color2hex(s.color_state_starting) 
			color_state_starting_selected = e2color2hex(s.color_state_starting_selected)
			color_state_running = e2color2hex(s.color_state_running) 
			color_state_running_selected = e2color2hex(s.color_state_running_selected)
			color_state_recording = e2color2hex(s.color_state_recording) 
			color_state_recording_selected = e2color2hex(s.color_state_recording_selected)
			color_state_finished = e2color2hex(s.color_state_finished) 
			color_state_finished_selected = e2color2hex(s.color_state_finished_selected)
			color_state_disabled = e2color2hex(s.color_state_disabled) 
			color_state_disabled_selected = e2color2hex(s.color_state_disabled_selected)
			color_state_unknown = e2color2hex(pzyP4TsettingsComponent.color_state_unknown)
			color_state_unknown_selected = e2color2hex(pzyP4TsettingsComponent.color_state_unknown_selected)
			color_title_filter_disabled = e2color2hex(s.color_title_filter_disabled)

			
		#Apply Icons
		#pzyP4TshowIcons = s.showIcons

		#autostart(1)
		#autostart(0)

		self.Exit()


	def abort(self):
		print "[pzyP4T] ... Screen closed ..."


	def Exit(self):
		self.close(True)

		
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################


class PzyP4TFilterEditor(Screen, ConfigListScreen):
	def __init__(self, session, cur_filterComponent=None):
		Screen.__init__(self, session)
		self.skinName = ["PzyP4TFilterEditor","TimerEntry"]
		
		self.session = session
		self.cur_filterComponent = cur_filterComponent[0] #(tpc,0)
		#print "####################### cur_filterComponent: \n",repr(cur_filterComponent)
				
		self.configList = None
		self.config = ConfigList([],session)
		self["config"] = self.config 
		
		self["VKeyIcon"] = Pixmap()
		
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()		
		
		self.color_preview = Label(_("This Is Your Current Color"))
		self["color_preview"] = self.color_preview

		
		#self.cur_filterComponent=pzyP4TFilterComponent() #test
		f = self.cur_filterComponent
		if f:
			#edit
			self.filter_disabled = NoSave(ConfigSelection(default=str(f.disabled), choices=[("True","yes"), ("False","no")]))
			self.filter_filterTitle = NoSave(ConfigText(default=str(f.filterTitle), fixed_size=False, visible_width=40))
			self.filter_searchString = NoSave(ConfigText(default=str(f.searchString), fixed_size=False, visible_width=40))
			self.filter_searchpart = NoSave(ConfigSelection(default=str(f.searchpart), choices=[("True","yes"), ("False","no")]))
			self.filter_case_insensitive = NoSave(ConfigSelection(default=str(f.case_insensitive), choices=[("True","yes"), ("False","no")]))
			self.filter_use_servicename = NoSave(ConfigSelection(default=str(f.use_servicename), choices=[("True","yes"), ("False","no")]))
			self.filter_show_servicename = NoSave(ConfigSelection(default=str(f.show_servicename), choices=[("True","yes"), ("False","no")]))

			if f.justremind and \
			   f.justplay and \
			   f.justrecord:
				cur_setting = "All"
				
			elif f.justremind:
				cur_setting = "Reminder"
				
			elif f.justplay:
				cur_setting = "Zap"
				
			else:
				cur_setting = "Recording"
			self.filter_typ = NoSave(ConfigSelection(default=cur_setting,choices=[("All","All"),("Reminder","Reminder"), ("Zap","Zap"),("Recording","Recording")]))
		else:
			self.Exit()
		
		
		self["actions"] = NumberActionMap(["ColorActions","SetupActions","VirtualKeyboardActions","ChannelSelectEPGActions"],
		                            {       "green": self.save_Configuration,
		                                    "cancel": self.Exit,
		                                    #"red": self.Exit,
		                                    ##"blue": self.
		                                    #"showEPGList": self.key_Info,
		                                    "1": self.keyNumberGlobal,
		                                    "2": self.keyNumberGlobal,
		                                    "3": self.keyNumberGlobal,
		                                    "4": self.keyNumberGlobal,
		                                    "5": self.keyNumberGlobal,
		                                    "6": self.keyNumberGlobal,
		                                    "7": self.keyNumberGlobal,
		                                    "8": self.keyNumberGlobal,
		                                    "9": self.keyNumberGlobal,
		                                    "0": self.keyNumberGlobal,
		                                    #"ok": self.key_ok
		                                    }, 0)

		self.setTitle("Timer Filter Setup")
		self.onClose.append(self.abort)

		self.configList = self.fillConfigList()
		ConfigListScreen.__init__(self, self.configList)

		#########################################################################

		
	def key_ok(self):
		self.KeyText()
		
		
	def KeyText(self):
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title = self["config"].getCurrent()[0], text = self["config"].getCurrent()[1].getValue())

		
	def VirtualKeyBoardCallback(self, callback = None):
		ConfigListScreen.VirtualKeyBoardCallback(self,callback)


	def keyLeft(self):
		ConfigListScreen.keyLeft(self)


	def keyRight(self):
		ConfigListScreen.keyRight(self)


	def keyNumberGlobal(self, number):
		ConfigListScreen.keyNumberGlobal(self,number)
		

	def keyGotAscii(self):
		ConfigListScreen.keyGotAscii(self)

	#########################################################################
			
	def fillConfigList(self):
		if self.cur_filterComponent:
			service_ref_name = "[%s]" %self.cur_filterComponent.service_ref_name
		else:
			service_ref_name = ""
			
		list = []
		list.append(getConfigListEntry(_("Filter Disabled:"), self.filter_disabled))
		list.append(getConfigListEntry(_("Title:"), self.filter_filterTitle))
		list.append(getConfigListEntry(_("Search For:"), self.filter_searchString))
		list.append(getConfigListEntry(_("Partial Search:") + ":", self.filter_searchpart))
		list.append(getConfigListEntry(_("Case Insensitive:"), self.filter_case_insensitive))
		list.append(getConfigListEntry(_("Use Servicename  %s" %service_ref_name) + ":", self.filter_use_servicename))
		list.append(getConfigListEntry(_("Show Servicename:"), self.filter_show_servicename))
		list.append(getConfigListEntry(_("Timer-Typ:"), self.filter_typ))
		
		return list
	
		
	def save_Configuration(self):
		global pzyP4T_writeSettings
		
		#if self["config"].isChanged():
			#pzyP4T_writeSettings = True
			
		f = self.cur_filterComponent
		f.disabled = eval(self.filter_disabled.value)
		f.filterTitle = str(self.filter_filterTitle.value)
		f.searchString = str(self.filter_searchString.value)
		f.searchpart = eval(self.filter_searchpart.value)
		f.case_insensitive = eval(self.filter_case_insensitive.value)
		f.use_servicename = eval(self.filter_use_servicename.value)
		f.show_servicename = eval(self.filter_show_servicename.value)

		cur_setting = str(self.filter_typ.value) #valuelist[7]
		if cur_setting == "Reminder":
			f.justremind = True
			f.justplay = False
			f.justrecord = False
				
		elif cur_setting == "Zap":
			f.justremind = False
			f.justplay = True
			f.justrecord = False
		
		elif cur_setting == "Recording":
			f.justremind = False
			f.justplay = False
			f.justrecord = True
		else:
			#All, only in filterComponent
			f.justremind = True
			f.justplay = True
			f.justrecord = True
			
		self.Exit(f)


	def abort(self):
		print "[pzyP4T] ... Screen closed ..."


	def Exit(self,tpc=None):
		self.close(tpc)


###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
		

class xmlconfig():
	def __init__(self):
		pass
		
	def readXml(self,filename=PZYP4T_XML_CONFIG):
		if not exists(PZYP4T_XML_CONFIG):
			print("[pzyP4T] No configuration file present")
			return False

		configuration = xml_parser(filename).getroot()
		
		lst=[]
		parseConfig(
			configuration,
			lst,
			configuration.get("version")
		)
		return True
		
	
	def getXml(self):
		
		lst = []
		return buildConfig(lst)

	
	def writeXml(self):
		with open(PZYP4T_XML_CONFIG, 'w') as config:
			config.writelines("".join(self.getXml()))


def parseConfig(configuration, list, version = None, uniqueTimerId = 0, defaultTimer = None):
	global pzyP4TsettingsComponent
	
	ctr=1
	for filterComponent in configuration.findall("filter"):
		tpc = pzyP4TFilterComponent() #ok
		if parseEntry(filterComponent, tpc):
			list.append((tpc,ctr))
			ctr +=1
	
	#s=pzyP4TSettings() #test
	
	s = pzyP4TsettingsComponent
	s.filterComponentList = list
	
	el = configuration.find("settings")
	s.showIcons = bool(int(el.get("showIcons", s.showIcons)))
	s.showEventEit = bool(int(el.get("showEventEit", s.showEventEit)))
	s.use_skin_colors = bool(int(el.get("use_skin_colors", s.use_skin_colors)))
	
	s.showEventDesc = bool(int(el.get("showEventDesc", s.showEventDesc)))
	#s.use_uniForegroundSelected = bool(int(el.get("use_uniForegroundSelected", s.use_uniForegroundSelected)))
	
	el = configuration.find("colors")
	s.color_service = str(el.get("color_service", s.color_service))
	s.color_service_selected = str(el.get("color_service_selected", s.color_service_selected))
	s.color_title = str(el.get("color_title", s.color_title))
	s.color_title_selected = str(el.get("color_title_selected", s.color_title_selected))
	s.color_title_filter_disabled = str(el.get("color_title_filter_disabled", s.color_title_filter_disabled))
	s.color_eventDesc = str(el.get("color_eventDesc", s.color_eventDesc))
	s.color_eventDesc_selected = str(el.get("color_eventDesc_selected", s.color_eventDesc_selected))
	s.color_time = str(el.get("color_time", s.color_time))
	s.color_time_selected = str(el.get("color_time_selected", s.color_time_selected))
	s.color_time_short = str(el.get("color_time_short", s.color_time_short))
	s.color_time_short_selected = str(el.get("color_time_short_selected", s.color_time_short_selected))
	s.color_time_record = str(el.get("color_time_record", s.color_time_record))
	s.color_time_record_selected = str(el.get("color_time_record_selected", s.color_time_record_selected))
	
	s.color_tuner = str(el.get("color_tuner", s.color_tuner))
	s.color_tuner_selected = str(el.get("color_tuner_selected", s.color_tuner_selected))
	s.color_orbital = str(el.get("color_orbital", s.color_orbital))
	s.color_orbital_selected = str(el.get("color_orbital_selected", s.color_orbital_selected))
	
	s.color_eventeit = str(el.get("color_eventeit", s.color_eventeit))
	s.color_eventeit_selected = str(el.get("color_eventeit_selected", s.color_eventeit_selected))
	
	s.color_state_disabled = str(el.get("color_state_disabled", s.color_state_disabled))
	s.color_state_disabled_selected = str(el.get("color_state_disabled_selected", s.color_state_disabled_selected))
	s.color_state_waiting = str(el.get("color_state_waiting", s.color_state_waiting))
	s.color_state_waiting_selected = str(el.get("color_state_waiting_selected", s.color_state_waiting_selected))
	s.color_state_waiting_long = str(el.get("color_state_waiting_long", s.color_state_waiting_long))
	s.color_state_waiting_long_selected = str(el.get("color_state_waiting_long_selected", s.color_state_waiting_long_selected))
	s.color_state_starting = str(el.get("color_state_starting", s.color_state_starting))
	s.color_state_starting_selected = str(el.get("color_state_starting_selected", s.color_state_starting_selected))
	s.color_state_running = str(el.get("color_state_running", s.color_state_running))
	s.color_state_running_selected = str(el.get("color_state_running_selected", s.color_state_running_selected))
	s.color_state_recording = str(el.get("color_state_recording", s.color_state_recording))
	s.color_state_recording_selected = str(el.get("color_state_recording_selected", s.color_state_recording_selected))
	s.color_state_unknown = str(el.get("color_state_unknown", s.color_state_unknown))
	s.color_state_unknown_selected = str(el.get("color_state_unknown_selected", s.color_state_unknown_selected))
	s.color_state_finished = str(el.get("color_state_finished", s.color_state_finished))
	s.color_state_finished_selected = str(el.get("color_state_finished_selected", s.color_state_finished_selected))


def buildConfig(list):
	s = pzyP4TsettingsComponent
	filters = s.filterComponentList

	list = ['<?xml version="1.0" encoding="UTF-8"?> \n\n<pzyP4T version="', PZYP4T_CONFIG_VERSION, '"> \n\n']

	append = list.append
	extend = list.extend

	append('<settings \n')
	append('\t showIcons="%s" \n' %str(int(s.showIcons)) )
	append('\t showEventEit="%s" \n' %str(int(s.showEventEit)) )
	append('\t use_skin_colors="%s" \n' %str(int(s.use_skin_colors)) )
	append('\t showEventDesc="%s"> \n' %str(int(s.showEventDesc)) )
	#append('\t use_uniForegroundSelected="%s"> \n' %str(int(s.use_uniForegroundSelected)) )
	append('</settings> \n\n')

	append('<colors \n')
	append('\t color_title="%s" \n' %stringToXML(s.color_title) )
	append('\t color_title_selected="%s" \n' %stringToXML(s.color_title_selected) )
	append('\t color_title_filter_disabled="%s" \n' %stringToXML(s.color_title_filter_disabled) )
	append('\t color_eventDesc="%s" \n' %stringToXML(s.color_eventDesc) )
	append('\t color_eventDesc_selected="%s" \n' %stringToXML(s.color_eventDesc_selected) )
	append('\t color_service="%s" \n' %stringToXML(s.color_service) )
	append('\t color_service_selected="%s" \n' %stringToXML(s.color_service_selected) )
	append('\t color_time="%s" \n' %stringToXML(s.color_time) )
	append('\t color_time_selected="%s" \n' %stringToXML(s.color_time_selected) )
	append('\t color_time_short="%s" \n' %stringToXML(s.color_time_short) )
	append('\t color_time_short_selected="%s" \n' %stringToXML(s.color_time_short_selected) )
	append('\t color_time_record="%s" \n' %stringToXML(s.color_time_record) )
	append('\t color_time_record_selected="%s" \n' %stringToXML(s.color_time_record_selected) )

	append('\t color_tuner="%s" \n' %stringToXML(s.color_tuner) )
	append('\t color_tuner_selected="%s" \n' %stringToXML(s.color_tuner_selected) )
	append('\t color_orbital="%s" \n' %stringToXML(s.color_orbital) )
	append('\t color_orbital_selected="%s" \n' %stringToXML(s.color_orbital_selected) )

	append('\t color_eventeit="%s" \n' %stringToXML(s.color_eventeit) )
	append('\t color_eventeit_selected="%s" \n' %stringToXML(s.color_eventeit_selected) )

	append('\t color_state_waiting="%s" \n' %stringToXML(s.color_state_waiting) )
	append('\t color_state_waiting_selected="%s" \n' %stringToXML(s.color_state_waiting_selected) )
	append('\t color_state_waiting_long="%s" \n' %stringToXML(s.color_state_waiting_long) )
	append('\t color_state_waiting_long_selected="%s" \n' %stringToXML(s.color_state_waiting_long_selected) )
	append('\t color_state_starting="%s" \n' %stringToXML(s.color_state_starting) )
	append('\t color_state_starting_selected="%s" \n' %stringToXML(s.color_state_starting_selected) )
	append('\t color_state_running="%s" \n' %stringToXML(s.color_state_running) )
	append('\t color_state_running_selected="%s" \n' %stringToXML(s.color_state_running_selected) )
	append('\t color_state_recording="%s" \n' %stringToXML(s.color_state_recording) )
	append('\t color_state_recording_selected="%s" \n' %stringToXML(s.color_state_recording_selected) )
	append('\t color_state_finished="%s" \n' %stringToXML(s.color_state_finished) )
	append('\t color_state_finished_selected="%s" \n' %stringToXML(s.color_state_finished_selected) )
	append('\t color_state_disabled="%s" \n' %stringToXML(s.color_state_disabled) )
	append('\t color_state_disabled_selected="%s" \n' %stringToXML(s.color_state_disabled_selected) )
	append('\t color_state_unknown="%s"> \n' %stringToXML(s.color_state_unknown) )
	append('\t color_state_unknown_selected="%s"> \n' %stringToXML(s.color_state_unknown_selected) )
	append('</colors> \n\n')


	for tpc in filters:
		if not tpc:
			return
		
		f = tpc[0]

		append('<filter ')
		
		append('name="%s" ' %stringToXML(f.filterTitle) )
		
		append('match="%s" ' %stringToXML(f.searchString) )

		append('disabled="%s" ' %str(int(f.disabled)) )

		append('searchpartial="%s" ' %str(int(f.searchpart)) )

		append('case_insensitive="%s" ' %str(int(f.case_insensitive)) )

		append('justplay="%s" ' %str(int(f.justplay)) )

		append('justremind="%s" ' %str(int(f.justremind)) )

		append('justrecord="%s" ' %str(int(f.justrecord)) )
			
		#if filter.zapbeforerecord:
			#extend((' zapbeforerecord="', str(filter.getZapbeforerecord()), '"'))

		append(' use_servicename="%s" ' %str(int(f.use_servicename)) )

		append(' show_servicename="%s" ' %str(int(f.show_servicename)) )
			
		append(' service_ref_name="%s" ' %stringToXML(f.service_ref_name) )			

		append('> \n')

		append('</filter> \n\n')

	append('</pzyP4T> \n')

	return list
		

def parseEntry(element, tpc, defaults = False):
	#tpc = pzyP4TFilterComponent() #test

	tpc.filterTitle = str(element.get("name", ""))
	
	tpc.searchString = str(element.get("match", ""))
	if not tpc.searchString:
		print "[pzyP4T] Parsing Error: ",tpc.filterTitle
		return False

	tpc.disabled = bool(int(element.get("disabled", tpc.disabled)))

	tpc.searchpart = bool(int(element.get("searchPartial", tpc.searchpart)))
	tpc.case_insensitive = bool(int(element.get("case_insensitive", tpc.case_insensitive)))

	tpc.justremind = bool(int(element.get("justremind", tpc.justremind)))
	tpc.justplay = bool(int(element.get("justplay", tpc.justplay)))
	tpc.justrecord = bool(int(element.get("justrecord", tpc.justrecord)))

	tpc.use_servicename = bool(int(element.get("use_servicename", tpc.use_servicename)))
	tpc.show_servicename = bool(int(element.get("show_servicename", tpc.show_servicename)))
	tpc.service_ref_name = str(element.get("service_ref_name", tpc.service_ref_name))

	return True



###################################################################################################################################
###################################################################################################################################
###################################################################################################################################



class PzyP4TChoiceList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent) 
		
		self.list = list
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setItemHeight(25)
		self.l.setBuildFunc(self.buildChoiceEntry)
		self.selection = selection	

		self.width = 1200
		self.height = 70
		
		self.iconpos_x = 5
		self.iconpos_y = 20
		
		self.iconwidth = 40
		self.iconheight = 40
		
		self.textpos_x = 60
		self.textpos_y = 0


	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
			
		
	def applySkin(self,desktop,parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
					
				elif attrib == "itemHeight":
					val = int(value)
					self.l.setItemHeight(val)
					self.height = val
				
				elif attrib == "iconpos":
					ep = parsePosition(value, ((1,1),(1,1))  )#ePoint
					self.iconpos_x = int(ep.x())
					self.iconpos_y = int(ep.y())
					
				elif attrib == "iconsize":
					es = parseSize(value, ((1,1),(1,1))) #eSize
					self.iconwidth = int(es.width())
					self.iconheight = int(es.height())
					
				elif attrib == "textpos":
					ep = parsePosition(value, ((1,1),(1,1)))
					self.textpos_x = int(ep.x())
					self.textpos_y = int(ep.y())
					
				elif attrib == "size":
					es = parseSize(value, ((1,1),(1,1)))
					self.width = int(es.width())
					##self.height = int(es.height())
					attribs.append((attrib, value))
					
				else:
					attribs.append((attrib, value))
					
		self.skinAttributes = attribs
		return MenuList.applySkin(self,desktop,parent)


	def buildChoiceEntry(self, key = "", text = ["--"]):
		res = [ text ]
		if text[0] == "--":
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.textpos_x, self.textpos_y, self.width, self.height, 0, RT_HALIGN_LEFT, "-"*200))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.textpos_x, self.textpos_y, self.width-self.textpos_x, self.height, 0, RT_HALIGN_LEFT, text[0]))
		
			png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/key_" + key + ".png"))
			if png is not None:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconpos_x, self.iconpos_y, self.iconwidth, self.iconheight, png))
		
		return res	
	
###################################################################################################################################


class ChoiceBoxPlus(Screen):
	
	def __init__(self, session, title = "", list = [], keys = None, selection = 0, skin_name = []):
		Screen.__init__(self, session)

		self["VKeyIcon"] = Pixmap()
		
		self.lcd_xres = None
		self.lcd_xres=self.readlcdxres()
		self["text"] = Label(title)
		self.list = []
		self.summarylist = []
		if keys is None:
			self.__keys = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "red", "green", "yellow", "blue" , "info"] + (len(list) - 10) * [""]
		else:
			self.__keys = keys + (len(list) - len(keys)) * [""]
			
		self.keymap = {}
		pos = 0
		for x in list:
			strpos = str(self.__keys[pos])
			self.list.append((strpos, x))
			if self.__keys[pos] != "":
				self.keymap[self.__keys[pos]] = list[pos]
			self.summarylist.append((self.__keys[pos],x[0]))
			pos += 1
			
		self["list"] = PzyP4TChoiceList(list = self.list, selection = selection)
		self["summary_list"] = StaticText()
		self.updateSummary(selection)
		
		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "ColorActions", "DirectionActions"], 
		{
			"ok": self.go,
			"back": self.cancel,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal,
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"up": self.up,
			"down": self.down
		}, -1)
		
		
		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.key_INFO
			}
		)		
		
		self["VirtualKeyboardActions"] = ActionMap(["VirtualKeyboardActions"],
			{
				"showVirtualKeyboard": self.key_TEXT
			}
		)	
		
		#self["PiPSetupActions"] = ActionMap(["PiPSetupActions"],
			#{
		                #"size+": self.key_bouq_pl,
		                #"size-": self.key_bouq_min
			#}
		#)		
		
		self["InfobarChannelSelection"] = ActionMap(["InfobarChannelSelection"],
			{
				"historyNext": self.key_greater,
		                "historyBack": self.key_less
			}
		)
		
		self.onFirstExecBegin.append(self.first_start)
	
	
	def first_start(self):
		self["list"].moveToIndex(0)
	
		
	def keyLeft(self):
		pass
	
	
	def keyRight(self):
		pass

	
	def up(self):
		if len(self["list"].list) > 0:
			while 1:
				self["list"].instance.moveSelection(self["list"].instance.moveUp)
				self.updateSummary(self["list"].l.getCurrentSelectionIndex())
				if self["list"].l.getCurrentSelection()[1][0] != "--" or self["list"].l.getCurrentSelectionIndex() == 0: #[0][0]
					break

	def down(self):
		if len(self["list"].list) > 0: #("key",("text",ret_func))
			while 1:
				self["list"].instance.moveSelection(self["list"].instance.moveDown)
				self.updateSummary(self["list"].l.getCurrentSelectionIndex())
				if self["list"].l.getCurrentSelection()[1][0] != "--" or self["list"].l.getCurrentSelectionIndex() == len(self["list"].list) - 1:
					break
				
	
	#def key_bouq_pl(self):
		##self.goKey("")

		
	#def key_bouq_min(self):
		##self.goKey("")
	
	
	def key_greater(self):
		self.goKey(">")

		
	def key_less(self):
		self.goKey("<")

		
	def key_INFO(self):
		self.goKey("info")

		
	def key_TEXT(self):
		self.goKey("text")
		
		
	def keyNumberGlobal(self, number):
		self.goKey(str(number))


	def go(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			self.goEntry(cursel[1])
		else:
			self.cancel()


	def goEntry(self, entry):
		if len(entry) > 2 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			# CALLFUNC wants to have the current selection as argument
			arg = self["list"].l.getCurrentSelection()[0]
			entry[2](arg)
		else:
			self.close(entry)

			
	def goKey(self, key):
		if self.keymap.has_key(key):
			entry = self.keymap[key]
			self.goEntry(entry)


	def keyRed(self):
		self.goKey("red")

		
	def keyGreen(self):
		self.goKey("green")

		
	def keyYellow(self):
		self.goKey("yellow")

		
	def keyBlue(self):
		self.goKey("blue")

		
	def updateSummary(self, curpos=0):
		pos = 0
		summarytext = ""
		for entry in self.summarylist:
			if self.lcd_xres is not None and self.lcd_xres > 140:
				if pos > curpos-2 and pos < curpos+5:
					if pos == curpos:
						summarytext += ">"
					else:
						summarytext += entry[0]
					summarytext += ' ' + entry[1] + '\n'
			else:
				if pos == curpos:
					summarytext += entry[0]+' '+ entry[1]
			pos += 1
		self["summary_list"].setText(summarytext)

		
	def cancel(self):
		self.close(None)

		
	def readlcdxres(self):
		try:
			fd = open("/proc/stb/lcd/xres","r")
			value = int(fd.read().strip(),16)
			fd.close()
			return value
		except:
			return None

###################################################################################################################################
		
		
class SkinableMenuList(MenuList):
	def __init__(self, list=[], enableWrapAround=True, content=eListboxPythonMultiContent):
		MenuList.__init__(self, list, enableWrapAround, content)

		self.l.setFont(0, gFont("Regular", 20))
		self.l.setItemHeight(60)
		self.l.setBuildFunc(self.buildEntry)
		self.list=list
		
		self.textpos_x = 0
		self.textpos_y = 0
		self.textwidth = None
		self.textheight = None
		self.textalign = RT_HALIGN_LEFT|RT_VALIGN_TOP #|RT_WRAP
	
		
	def applySkin(self,desktop,parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
					
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
					
				elif attrib == "textAlign":
					self.textalign = eval(value)
					
				elif attrib == "textPos":
					ep = parsePosition(value, ((1,1),(1,1)))
					self.textpos_x = int(ep.x())
					self.textpos_y = int(ep.y())
					
				elif attrib == "textSize":
					es = parseSize(value, ((1,1),(1,1)))
					self.textwidth = int(es.width())
					self.textheight = int(es.height())
					
				else:
					attribs.append((attrib, value))
					
		self.skinAttributes = attribs
		return MenuList.applySkin(self,desktop,parent)

	
	def buildEntry(self,element,x):
		if not self.textwidth:
			self.textwidth = self.l.getItemSize().width()
			self.textheight = self.l.getItemSize().height()

		menuEntry = [(element)]
		menuEntry.append(MultiContentEntryText(pos=(self.textpos_x, self.textpos_y), size=(self.textwidth, self.textheight), font=0, flags=self.textalign, text=element))
		return menuEntry

	
	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur

	
	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1
			
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################
			
		
class LogEntryDate(StaticText):
	def __init__(self):
		StaticText.__init__(self)
		self.time = None #ClockToText-Renderer needs 'time'
		
	def setTime(self,date):
		self.time = date
		self.changed((self.CHANGED_ALL,))
		

class PzyTimerLog(TimerLog):
	def __init__(self, session, timer):
		TimerLog.__init__(self, session, timer)
		self.skinName = ["PzyTimerLog"]
		
		self["logentry_date"] = LogEntryDate()
		
		self.loglist = SkinableMenuList(self.list)
		self["loglist"] = self.loglist
		
		self.onFirstExecBegin.append(self.first_start)
	
		
	def first_start(self):
		self["loglist"].moveToIndex(0)

		
	def updateText(self):
		if self.list:
			cur = self.loglist.getCurrent()[1]
			self["logentry"].setText(str(cur[2]))
			self["logentry_date"].setTime(cur[0])
		else:
			self["logentry"].setText("")
			self["logentry_date"].setTime(None)
		

	def fillLogList(self):
		self.list = [(str(strftime("%Y-%m-%d  %H:%M", localtime(x[0])) + " - " + x[2]), x) for x in self.log_entries]
		
		
##############################################################################################################################################################

if pzy_bln_DreamOS:
	from Screens.ChoiceBox import ChoiceBox
	cbx = ChoiceBox
	#cbx = ChoiceBoxPlus
else:
	cbx = ChoiceBoxPlus		