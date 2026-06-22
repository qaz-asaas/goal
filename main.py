from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle
from kivy.utils import platform
from kivy.logger import Logger
import json
import os
import traceback
import sys

# ---- 全局崩溃保护 ----
def handle_exception(exc_type, exc_value, exc_tb):
    """捕获所有未处理异常，防止闪退"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    Logger.error(f'Global Exception: {error_msg}')
    try:
        with open(os.path.join(os.environ.get('EXTERNAL_STORAGE', '/sdcard'), 'goal_error.log'), 'w') as f:
            f.write(error_msg)
    except:
        pass

sys.excepthook = handle_exception

# ---- Plyer filechooser ----
HAS_PLYER = False
try:
    from plyer import filechooser
    HAS_PLYER = True
except Exception:
    pass

class GoalItem(BoxLayout):
    name = StringProperty('')
    target_amount = NumericProperty(0)
    current_amount = NumericProperty(0)
    remaining_amount = NumericProperty(0)
    progress = NumericProperty(0)
    
    def __init__(self, name, target_amount, current_amount=0, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.target_amount = target_amount
        self.current_amount = current_amount
        self.update_remaining()
    
    def update_remaining(self):
        self.remaining_amount = max(0, self.target_amount - self.current_amount)
        if self.target_amount > 0:
            self.progress = min(100, max(0, (self.current_amount / self.target_amount) * 100))
        else:
            self.progress = 0

class GoalApp(App):
    def get_data_dir(self):
        """
        获取应用数据目录。
        Android: 使用 App 私有目录 /data/data/<package>/files
        PC: 使用 user_data_dir
        注意：此方法不能在 build() 之前调用
        """
        try:
            if platform == 'android':
                # 方法1: 使用 pyjnius 获取 Context
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity
                if context:
                    files_dir = context.getFilesDir().getAbsolutePath()
                    if not os.path.exists(files_dir):
                        os.makedirs(files_dir)
                    return files_dir
                # 备用方案: 环境变量
                data_dir = os.environ.get('ANDROID_APP_PATH', '/data/data/org.example.goal/files')
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                return data_dir
            else:
                return self.user_data_dir
        except Exception as e:
            Logger.error(f'get_data_dir error: {e}')
            # 最终兜底
            return self.user_data_dir

    def build(self):
        Window.clearcolor = (0.9, 0.95, 1, 1)
        
        self.goals = []
        self.load_goals()
        self.user_info = self.load_user_info()
        
        self.root = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        self.create_project_layout()
        self.create_profile_layout()
        
        self.nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60)
        self.nav_bar.add_widget(Button(
            text='\u9879\u76ee', font_size=18, size_hint=(0.5, 1), 
            background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1),
            on_press=lambda x: self.switch_to_project()
        ))
        self.nav_bar.add_widget(Button(
            text='\u6211\u7684', font_size=18, size_hint=(0.5, 1), 
            background_color=(0.9, 0.9, 0.9, 1), color=(0, 0, 0, 1),
            on_press=lambda x: self.switch_to_profile()
        ))
        
        self.root.add_widget(self.project_layout)
        self.root.add_widget(self.nav_bar)
        
        self.refresh_goals_list()
        return self.root
    
    def create_project_layout(self):
        self.project_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        header = Label(text='\u76ee\u6807\u50a8\u84c4', font_size=24, size_hint=(1, None), height=60)
        self.project_layout.add_widget(header)
        
        self.add_btn = Button(text='+ \u6dfb\u52a0\u76ee\u6807', size_hint=(1, None), height=50, 
                             background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1))
        self.add_btn.bind(on_press=self.show_add_popup)
        self.project_layout.add_widget(self.add_btn)
        
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.goals_list = BoxLayout(orientation='vertical', size_hint=(1, None), padding=10, spacing=10)
        self.goals_list.bind(minimum_height=self.goals_list.setter('height'))
        self.scroll_view.add_widget(self.goals_list)
        self.project_layout.add_widget(self.scroll_view)
    
    def create_profile_layout(self):
        self.profile_layout = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=20)
        
        header = Label(text='\u4e2a\u4eba\u4e2d\u5fc3', font_size=24, size_hint=(1, None), height=60)
        self.profile_layout.add_widget(header)
        
        self.avatar_btn = Button(text='\ud83d\ude0a', font_size=72, size_hint=(None, None), size=(120, 120),
                                background_color=(0, 0, 0, 0), pos_hint={'center_x': 0.5})
        self.avatar_btn.bind(on_press=self.select_avatar)
        self.profile_layout.add_widget(self.avatar_btn)
        
        self.name_input = TextInput(text=self.user_info.get('name', ''), hint_text='\u8f93\u5165\u6635\u79f0',
                                   size_hint=(1, None), height=50, font_size=18)
        self.profile_layout.add_widget(self.name_input)
        
        save_btn = Button(text='\u4fdd\u5b58', size_hint=(1, None), height=50,
                         background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1))
        save_btn.bind(on_press=self.save_user_info)
        self.profile_layout.add_widget(save_btn)
    
    def switch_to_project(self):
        self.root.clear_widgets()
        self.root.add_widget(self.project_layout)
        self.root.add_widget(self.nav_bar)
    
    def switch_to_profile(self):
        self.root.clear_widgets()
        self.root.add_widget(self.profile_layout)
        self.root.add_widget(self.nav_bar)
    
    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.name_input_popup = TextInput(hint_text='\u76ee\u6807\u540d\u79f0', font_size=18)
        content.add_widget(self.name_input_popup)
        
        self.target_input = TextInput(hint_text='\u76ee\u6807\u91d1\u989d', font_size=18, input_filter='float')
        content.add_widget(self.target_input)
        
        buttons = BoxLayout(orientation='horizontal', spacing=10)
        buttons.add_widget(Button(text='\u53d6\u6d88', size_hint=(0.5, 1), 
                                  background_color=(0.8, 0.8, 0.8, 1), on_press=self.close_popup))
        buttons.add_widget(Button(text='\u786e\u5b9a', size_hint=(0.5, 1), 
                                  background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1),
                                  on_press=self.add_goal))
        content.add_widget(buttons)
        
        self.popup = Popup(title='\u6dfb\u52a0\u76ee\u6807', content=content, size_hint=(0.9, 0.5))
        self.popup.open()
    
    def close_popup(self, instance):
        self.popup.dismiss()
    
    def add_goal(self, instance):
        name = self.name_input_popup.text.strip()
        try:
            target = float(self.target_input.text)
        except:
            target = 0
        
        if name and target > 0:
            self.goals.append({'name': name, 'target': target, 'current': 0})
            self.save_goals()
            self.refresh_goals_list()
        self.popup.dismiss()
    
    def refresh_goals_list(self):
        self.goals_list.clear_widgets()
        
        for i, goal in enumerate(self.goals):
            item = BoxLayout(orientation='vertical', size_hint=(1, None), height=100, padding=10)
            
            with item.canvas.before:
                Color(1, 1, 1, 0.9)
                Rectangle(size=item.size, pos=item.pos)
            
            item.add_widget(Label(text=goal['name'], font_size=18, size_hint=(1, None), height=30))
            
            progress_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=40)
            progress_box.add_widget(Label(text=f"{goal['current']:.2f} / {goal['target']:.2f}", font_size=14))
            
            progress_bar = BoxLayout(size_hint=(1, None), height=10)
            with progress_bar.canvas.before:
                Color(0.9, 0.9, 0.9, 1)
                Rectangle(size=progress_bar.size, pos=progress_bar.pos)
            
            fill_width = min(1, goal['current'] / goal['target']) if goal['target'] > 0 else 0
            fill = BoxLayout(size_hint=(fill_width, 1))
            with fill.canvas.before:
                Color(0.2, 0.6, 0.8, 1)
                Rectangle(size=fill.size, pos=fill.pos)
            progress_bar.add_widget(fill)
            progress_box.add_widget(progress_bar)
            item.add_widget(progress_box)
            
            buttons = BoxLayout(orientation='horizontal', spacing=5)
            buttons.add_widget(Button(text='+', size_hint=(0.3, 1), height=30,
                                     background_color=(0.4, 0.8, 0.4, 1), color=(1, 1, 1, 1),
                                     on_press=lambda x, idx=i: self.show_add_amount(idx)))
            buttons.add_widget(Button(text='-', size_hint=(0.3, 1), height=30,
                                     background_color=(0.8, 0.4, 0.4, 1), color=(1, 1, 1, 1),
                                     on_press=lambda x, idx=i: self.show_delete(idx)))
            item.add_widget(buttons)
            
            self.goals_list.add_widget(item)
    
    def show_add_amount(self, index):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.amount_input = TextInput(hint_text='\u6dfb\u52a0\u91d1\u989d', font_size=18, input_filter='float')
        content.add_widget(self.amount_input)
        
        buttons = BoxLayout(orientation='horizontal', spacing=10)
        buttons.add_widget(Button(text='\u53d6\u6d88', size_hint=(0.5, 1), 
                                  background_color=(0.8, 0.8, 0.8, 1), on_press=self.close_popup))
        buttons.add_widget(Button(text='\u786e\u5b9a', size_hint=(0.5, 1), 
                                  background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1),
                                  on_press=lambda x: self.add_amount(index)))
        content.add_widget(buttons)
        
        self.popup = Popup(title='\u6dfb\u52a0\u91d1\u989d', content=content, size_hint=(0.9, 0.5))
        self.popup.open()
    
    def add_amount(self, index):
        try:
            amount = float(self.amount_input.text)
            if amount > 0:
                self.goals[index]['current'] += amount
                self.save_goals()
                self.refresh_goals_list()
        except:
            pass
        self.popup.dismiss()
    
    def show_delete(self, index):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(text='\u786e\u5b9a\u8981\u5220\u9664\u8fd9\u4e2a\u76ee\u6807\u5417\uff1f', font_size=18))
        
        buttons = BoxLayout(orientation='horizontal', spacing=10)
        buttons.add_widget(Button(text='\u53d6\u6d88', size_hint=(0.5, 1), 
                                  background_color=(0.8, 0.8, 0.8, 1), on_press=self.close_popup))
        buttons.add_widget(Button(text='\u5220\u9664', size_hint=(0.5, 1), 
                                  background_color=(0.8, 0.4, 0.4, 1), color=(1, 1, 1, 1),
                                  on_press=lambda x: self.delete_goal(index)))
        content.add_widget(buttons)
        
        self.popup = Popup(title='\u5220\u9664\u786e\u8ba4', content=content, size_hint=(0.9, 0.5))
        self.popup.open()
    
    def delete_goal(self, index):
        del self.goals[index]
        self.save_goals()
        self.refresh_goals_list()
        self.popup.dismiss()
    
    def select_avatar(self, instance):
        """选择头像 - Android 上安全处理"""
        try:
            if platform == 'android':
                # Android 上使用原生 Intent 选择图片
                from jnius import autoclass, cast
                from android import activity
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_PICK)
                intent.setType('image/*')
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                currentActivity.startActivityForResult(intent, 1001)
                
                def on_activity_result(request_code, result_code, data):
                    if request_code == 1001 and result_code == -1:  # RESULT_OK = -1
                        try:
                            uri = data.getData()
                            if uri:
                                self.user_info['avatar'] = uri.toString()
                                self.save_user_info(None)
                        except Exception as e:
                            Logger.error(f'avatar select error: {e}')
                    activity.unbind(on_activity_result=on_activity_result)
                
                activity.bind(on_activity_result=on_activity_result)
            elif HAS_PLYER:
                filechooser.open_file(on_selection=self.on_avatar_selected, filters=['*.png', '*.jpg', '*.jpeg'])
        except Exception as e:
            Logger.error(f'select_avatar error: {e}')
    
    def on_avatar_selected(self, selection):
        if selection:
            self.user_info['avatar'] = selection[0]
            self.save_user_info(None)
    
    def save_user_info(self, instance):
        self.user_info['name'] = self.name_input.text
        filepath = os.path.join(self.get_data_dir(), 'user_info.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.user_info, f, ensure_ascii=False)
    
    def load_user_info(self):
        try:
            filepath = os.path.join(self.get_data_dir(), 'user_info.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'name': '', 'avatar': ''}
    
    def save_goals(self):
        filepath = os.path.join(self.get_data_dir(), 'goals.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.goals, f, ensure_ascii=False)
    
    def load_goals(self):
        try:
            filepath = os.path.join(self.get_data_dir(), 'goals.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                self.goals = json.load(f)
        except:
            self.goals = []

if __name__ == '__main__':
    GoalApp().run()
