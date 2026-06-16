from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
import json
import os
import base64

try:
    from plyer import filechooser
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False
    Logger.warning('Plyer not available, image picker will use fallback')

resource_add_path(os.path.dirname(__file__))

font_paths = [
    r'C:\Windows\Fonts\simhei.ttf',
    r'C:\Windows\Fonts\msyh.ttf',
    '/system/fonts/DroidSansFallback.ttf',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
]

CHINESE_FONT = 'DejaVuSans'
for font_path in font_paths:
    if os.path.exists(font_path):
        LabelBase.register(name='ChineseFont', fn_regular=font_path)
        CHINESE_FONT = 'ChineseFont'
        break

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
            self.progress = (self.current_amount / self.target_amount) * 100
        else:
            self.progress = 0

class GoalApp(App):
    def build(self):
        from kivy.uix.floatlayout import FloatLayout
        
        Window.size = (400, 700)
        Window.title = '目标储蓄'
        
        self.goals = []
        self.load_goals()
        self.user_info = self.load_user_info()
        
        self.main_layout = FloatLayout()
        
        with self.main_layout.canvas.before:
            Color(0.9, 0.95, 1, 1)
            self.bg_rect = Rectangle(size=Window.size, pos=self.main_layout.pos)
        self.main_layout.bind(size=self.update_bg_rect, pos=self.update_bg_rect)
        
        self.content_layout = BoxLayout(orientation='vertical')
        
        self.header = Label(text='🎯 目标储蓄', font_size=24, bold=True, size_hint_y=None, height=50, font_name=CHINESE_FONT, color=(0.1, 0.3, 0.6, 1))
        
        self.add_button = Button(text='+ 添加目标', size_hint_y=None, height=50, background_color=(0.2, 0.6, 0.8, 1), font_name=CHINESE_FONT, font_size=18, color=(1, 1, 1, 1))
        self.add_button.bind(on_press=self.show_add_popup)
        
        self.scroll_view = ScrollView()
        self.goals_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        self.goals_layout.bind(minimum_height=self.goals_layout.setter('height'))
        self.scroll_view.add_widget(self.goals_layout)
        
        self.project_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.project_layout.add_widget(self.header)
        self.project_layout.add_widget(self.add_button)
        self.project_layout.add_widget(self.scroll_view)
        
        self.profile_layout = self.create_profile_layout()
        
        # 底部导航栏
        self.nav_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, padding=[10, 5, 10, 10], spacing=5)
        with self.nav_bar.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(size=self.nav_bar.size, pos=self.nav_bar.pos)
        self.nav_bar.bind(size=self.update_nav_bg, pos=self.update_nav_bg)
        
        # 项目按钮
        self.project_btn = Button(
            text='📋 项目', 
            font_name=CHINESE_FONT, 
            font_size=16, 
            size_hint_x=0.5, 
            background_color=(0.2, 0.6, 0.8, 1), 
            color=(1, 1, 1, 1),
            bold=True
        )
        self.project_btn.bind(on_press=self.switch_to_project)
        
        # 我的按钮
        self.profile_btn = Button(
            text='👤 我的', 
            font_name=CHINESE_FONT, 
            font_size=16, 
            size_hint_x=0.5, 
            background_color=(0.9, 0.9, 0.9, 1), 
            color=(0, 0, 0, 1),
            bold=True
        )
        self.profile_btn.bind(on_press=self.switch_to_profile)
        
        self.nav_bar.add_widget(self.project_btn)
        self.nav_bar.add_widget(self.profile_btn)
        
        # 先添加内容，再添加导航栏（导航栏在底部）
        self.content_layout.add_widget(self.project_layout)
        self.content_layout.add_widget(self.nav_bar)
        
        self.main_layout.add_widget(self.content_layout)
        
        self.refresh_goals_list()
        
        return self.main_layout
    
    def update_bg_rect(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos
    
    def update_nav_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 0.95)
            Rectangle(size=instance.size, pos=instance.pos)
    
    def create_profile_layout(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        header = Label(text='👤 个人中心', font_size=24, bold=True, size_hint_y=None, height=50, font_name=CHINESE_FONT, color=(0.1, 0.3, 0.6, 1))
        layout.add_widget(header)
        
        card = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None, height=220)
        with card.canvas.before:
            Color(1, 1, 1, 0.9)
            Rectangle(size=card.size, pos=card.pos)
        card.bind(size=self.update_card_bg, pos=self.update_card_bg)
        
        avatar_box = BoxLayout(orientation='vertical', size_hint_y=None, height=140)
        
        # 头像容器 - 可点击，直接选择图片
        from kivy.uix.behaviors import ButtonBehavior
        
        # 创建可点击的头像容器
        self.avatar_container = BoxLayout(size_hint_y=None, height=100)
        
        # 检查是否有图片头像
        avatar_data = self.user_info.get('avatar', '😊')
        if avatar_data.startswith('data:image') or (os.path.exists(avatar_data) if isinstance(avatar_data, str) else False):
            # 显示图片头像
            self.avatar_image = Image(source=avatar_data if os.path.exists(avatar_data) else '', allow_stretch=True, size_hint=(None, None), size=(100, 100))
            if avatar_data.startswith('data:image'):
                # Base64图片数据
                self.avatar_image = Image(allow_stretch=True, size_hint=(None, None), size=(100, 100))
                self.load_base64_avatar(avatar_data)
            self.avatar_container.add_widget(self.avatar_image)
        else:
            # 显示emoji头像
            self.avatar_label = Label(text=avatar_data, font_size=64, font_name=CHINESE_FONT, size_hint_y=None, height=100)
            self.avatar_container.add_widget(self.avatar_label)
        
        # 创建一个透明的按钮覆盖在头像上，使其可点击
        avatar_btn = Button(text='', size_hint=(1, 1), background_color=(0, 0, 0, 0), opacity=0)
        avatar_btn.bind(on_press=self.select_from_gallery)
        
        # 使用FloatLayout叠加按钮和头像
        from kivy.uix.floatlayout import FloatLayout
        avatar_float = FloatLayout(size_hint_y=None, height=100)
        avatar_float.add_widget(self.avatar_container)
        avatar_float.add_widget(avatar_btn)
        
        # 提示文字
        hint_label = Label(text='点击头像更换', font_name=CHINESE_FONT, font_size=12, color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=30)
        
        avatar_box.add_widget(avatar_float)
        avatar_box.add_widget(hint_label)
        card.add_widget(avatar_box)
        
        name_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        name_label = Label(text='昵称:', font_name=CHINESE_FONT, font_size=16, size_hint_x=0.3, color=(0, 0, 0, 1))
        self.name_input = TextInput(text=self.user_info.get('name', '用户'), font_name=CHINESE_FONT, font_size=16, size_hint_x=0.5)
        save_name_btn = Button(text='保存', font_name=CHINESE_FONT, font_size=14, size_hint_x=0.2, background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1))
        save_name_btn.bind(on_press=self.save_name)
        name_box.add_widget(name_label)
        name_box.add_widget(self.name_input)
        name_box.add_widget(save_name_btn)
        card.add_widget(name_box)
        
        layout.add_widget(card)
        
        stats_card = BoxLayout(orientation='vertical', padding=15, spacing=10, size_hint_y=None, height=140)
        with stats_card.canvas.before:
            Color(1, 1, 1, 0.9)
            Rectangle(size=stats_card.size, pos=stats_card.pos)
        stats_card.bind(size=self.update_card_bg, pos=self.update_card_bg)
        
        stats_header = Label(text='📊 统计信息', font_size=18, bold=True, font_name=CHINESE_FONT, color=(0.1, 0.3, 0.6, 1))
        stats_card.add_widget(stats_header)
        
        stats_box = GridLayout(cols=2, spacing=10, size_hint_y=None, height=80)
        stats_box.add_widget(Label(text='目标总数: ' + str(len(self.goals)), font_name=CHINESE_FONT, font_size=16, color=(0, 0, 0, 1)))
        total_target = sum(g['target'] for g in self.goals)
        total_current = sum(g['current'] for g in self.goals)
        stats_box.add_widget(Label(text='总目标金额: ' + str(total_target) + ' 元', font_name=CHINESE_FONT, font_size=16, color=(0, 0, 0, 1)))
        stats_box.add_widget(Label(text='已存金额: ' + str(total_current) + ' 元', font_name=CHINESE_FONT, font_size=16, color=(0, 0, 0, 1)))
        stats_box.add_widget(Label(text='完成比例: ' + str(int(total_current / total_target * 100) if total_target > 0 else 0) + '%', font_name=CHINESE_FONT, font_size=16, color=(0.2, 0.6, 0.8, 1)))
        stats_card.add_widget(stats_box)
        
        layout.add_widget(stats_card)
        
        return layout
    
    def load_base64_avatar(self, data_url):
        """加载Base64编码的图片头像"""
        try:
            # 解析data URL
            if data_url.startswith('data:image'):
                # 提取base64数据
                base64_data = data_url.split(',', 1)[1]
                image_data = base64.b64decode(base64_data)
                
                # 保存为临时文件
                temp_path = os.path.join(os.path.dirname(__file__), 'temp_avatar.png')
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                
                # 更新图片显示
                if hasattr(self, 'avatar_image'):
                    self.avatar_image.source = temp_path
        except Exception as e:
            Logger.error(f'Failed to load base64 avatar: {e}')
    
    def update_card_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 0.9)
            Rectangle(size=instance.size, pos=instance.pos)
    
    def switch_to_project(self, instance):
        # 移除当前页面
        if self.profile_layout in self.content_layout.children:
            self.content_layout.remove_widget(self.profile_layout)
        
        # 确保导航栏在底部
        if self.nav_bar in self.content_layout.children:
            self.content_layout.remove_widget(self.nav_bar)
        
        # 添加页面和导航栏
        self.content_layout.add_widget(self.project_layout)
        self.content_layout.add_widget(self.nav_bar)
        
        # 更新按钮状态
        self.project_btn.background_color = (0.2, 0.6, 0.8, 1)
        self.profile_btn.background_color = (0.9, 0.9, 0.9, 1)
        self.project_btn.color = (1, 1, 1, 1)
        self.profile_btn.color = (0, 0, 0, 1)
    
    def switch_to_profile(self, instance):
        # 移除当前页面
        if self.project_layout in self.content_layout.children:
            self.content_layout.remove_widget(self.project_layout)
        
        # 确保导航栏在底部
        if self.nav_bar in self.content_layout.children:
            self.content_layout.remove_widget(self.nav_bar)
        
        # 添加页面和导航栏
        self.content_layout.add_widget(self.profile_layout)
        self.content_layout.add_widget(self.nav_bar)
        
        # 更新按钮状态
        self.profile_btn.background_color = (0.2, 0.6, 0.8, 1)
        self.project_btn.background_color = (0.9, 0.9, 0.9, 1)
        self.profile_btn.color = (1, 1, 1, 1)
        self.project_btn.color = (0, 0, 0, 1)
    
    def select_from_gallery(self, instance):
        """从相册选择图片"""
        if HAS_PLYER:
            try:
                # 使用plyer的文件选择器
                filechooser.open_file(
                    title='选择头像图片',
                    filters=[('图片文件', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp')],
                    on_selection=self.on_image_selected
                )
            except Exception as e:
                Logger.error(f'Failed to open file chooser: {e}')
                self.show_error('无法打开相册')
        else:
            # 备用方案：使用系统文件对话框
            self.show_image_input_dialog()
    
    def on_image_selected(self, selection):
        """处理选择的图片"""
        if selection and len(selection) > 0:
            image_path = selection[0]
            self.process_selected_image(image_path)
    
    def show_image_input_dialog(self):
        """显示图片路径输入对话框（备用方案）"""
        input_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        label = Label(text='请输入图片路径:', font_name=CHINESE_FONT, font_size=16)
        input_layout.add_widget(label)
        
        path_input = TextInput(hint_text='例如: /sdcard/Pictures/avatar.jpg', font_name=CHINESE_FONT, font_size=14)
        input_layout.add_widget(path_input)
        
        btn_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=45)
        confirm_btn = Button(text='确定', font_name=CHINESE_FONT, background_color=(0.2, 0.6, 0.8, 1), color=(1, 1, 1, 1))
        cancel_btn = Button(text='取消', font_name=CHINESE_FONT, background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        btn_box.add_widget(confirm_btn)
        btn_box.add_widget(cancel_btn)
        input_layout.add_widget(btn_box)
        
        popup = Popup(title='输入图片路径', content=input_layout, size_hint=(0.9, 0.5))
        popup.title_font = CHINESE_FONT
        
        confirm_btn.bind(on_press=lambda _: self.process_selected_image(path_input.text))
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def process_selected_image(self, image_path):
        """处理选择的图片"""
        try:
            if not os.path.exists(image_path):
                self.show_error('图片文件不存在')
                return
            
            # 复制图片到应用目录
            import shutil
            avatar_dir = os.path.join(os.path.dirname(__file__), 'avatars')
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            
            avatar_path = os.path.join(avatar_dir, 'user_avatar.png')
            shutil.copy(image_path, avatar_path)
            
            # 更新头像显示
            self.update_avatar_display(avatar_path)
            
            # 保存头像路径
            self.user_info['avatar'] = avatar_path
            self.save_user_info()
            
            self.show_error('头像已更新')
            
        except Exception as e:
            Logger.error(f'Failed to process image: {e}')
            self.show_error('图片处理失败，请重试')
    
    def update_avatar_display(self, image_path):
        """更新头像显示"""
        # 清空当前头像容器
        self.avatar_container.clear_widgets()
        
        # 创建新的图片头像
        self.avatar_image = Image(source=image_path, allow_stretch=True, size_hint=(None, None), size=(100, 100))
        self.avatar_container.add_widget(self.avatar_image)
    
    def change_avatar(self, avatar):
        """更改表情头像"""
        # 清空当前头像容器
        self.avatar_container.clear_widgets()
        
        # 创建新的emoji头像
        self.avatar_label = Label(text=avatar, font_size=64, font_name=CHINESE_FONT, size_hint_y=None, height=100)
        self.avatar_container.add_widget(self.avatar_label)
        
        self.user_info['avatar'] = avatar
        self.save_user_info()
        self.avatar_popup.dismiss()
    
    def save_name(self, instance):
        self.user_info['name'] = self.name_input.text.strip()
        self.save_user_info()
        self.show_error('昵称已保存')
    
    def save_user_info(self):
        with open('user_info.json', 'w', encoding='utf-8') as f:
            json.dump(self.user_info, f, ensure_ascii=False)
    
    def load_user_info(self):
        if os.path.exists('user_info.json'):
            try:
                with open('user_info.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'name': '用户', 'avatar': '😊'}
        return {'name': '用户', 'avatar': '😊'}
    
    def refresh_goals_list(self):
        self.goals_layout.clear_widgets()
        
        for i, goal in enumerate(self.goals):
            goal_box = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=140, padding=10)
            with goal_box.canvas.before:
                Color(1, 1, 1, 0.9)
                Rectangle(size=goal_box.size, pos=goal_box.pos)
            goal_box.bind(size=self.update_goal_box_bg, pos=self.update_goal_box_bg)
            
            name_label = Label(text=goal['name'], font_size=18, bold=True, font_name=CHINESE_FONT, color=(0.1, 0.3, 0.6, 1))
            goal_box.add_widget(name_label)
            
            amount_box = GridLayout(cols=3, spacing=10)
            amount_box.add_widget(Label(text='目标: ' + str(goal["target"]) + ' 元', font_size=14, font_name=CHINESE_FONT, color=(0, 0, 0, 1)))
            amount_box.add_widget(Label(text='已存: ' + str(goal["current"]) + ' 元', font_size=14, font_name=CHINESE_FONT, color=(0, 0, 0, 1)))
            amount_box.add_widget(Label(text='还差: ' + str(goal["target"] - goal["current"]) + ' 元', font_size=14, color=(1, 0.5, 0, 1), font_name=CHINESE_FONT))
            goal_box.add_widget(amount_box)
            
            # 进度条容器
            progress_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=25)
            
            # 使用FloatLayout作为进度条，可以精确控制填充比例
            from kivy.uix.floatlayout import FloatLayout
            progress_bar = FloatLayout(size_hint_x=0.8, size_hint_y=None, height=20)
            
            # 进度条背景（灰色）
            progress_bg = BoxLayout(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            with progress_bg.canvas.before:
                Color(0.85, 0.85, 0.85, 1)
                Rectangle(size=progress_bg.size, pos=progress_bg.pos)
            progress_bg.bind(size=self.update_progress_bg_rect, pos=self.update_progress_bg_rect)
            
            # 进度条填充（蓝色）
            progress_ratio = min(1.0, (goal['current'] / goal['target']) if goal['target'] > 0 else 0)
            progress_fill = BoxLayout(size_hint=(progress_ratio, 1), pos_hint={'x': 0, 'y': 0})
            with progress_fill.canvas.before:
                Color(0.2, 0.6, 0.8, 1)
                Rectangle(size=progress_fill.size, pos=progress_fill.pos)
            progress_fill.bind(size=self.update_progress_fill_rect, pos=self.update_progress_fill_rect)
            
            progress_bar.add_widget(progress_bg)
            progress_bar.add_widget(progress_fill)
            
            # 进度百分比标签
            progress_label = Label(
                text=str(int(progress_ratio * 100)) + '%', 
                size_hint_x=0.2, 
                font_size=14, 
                font_name=CHINESE_FONT, 
                color=(0.2, 0.6, 0.8, 1),
                bold=True
            )
            
            progress_box.add_widget(progress_bar)
            progress_box.add_widget(progress_label)
            goal_box.add_widget(progress_box)
            
            button_box = BoxLayout(spacing=10)
            add_button = Button(text='+ 添加金额', size_hint_x=0.6, height=40, background_color=(0.3, 0.7, 0.3, 1), font_name=CHINESE_FONT, font_size=14, color=(1, 1, 1, 1))
            add_button.bind(on_press=lambda _, idx=i: self.show_add_amount_popup(idx))
            delete_button = Button(text='删除', size_hint_x=0.4, height=40, background_color=(0.8, 0.3, 0.3, 1), font_name=CHINESE_FONT, font_size=14, color=(1, 1, 1, 1))
            delete_button.bind(on_press=lambda _, idx=i: self.delete_goal(idx))
            button_box.add_widget(add_button)
            button_box.add_widget(delete_button)
            goal_box.add_widget(button_box)
            
            self.goals_layout.add_widget(goal_box)
    
    def update_goal_box_bg(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 0.9)
            Rectangle(size=instance.size, pos=instance.pos)
    
    def update_progress_bg_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            Rectangle(size=instance.size, pos=instance.pos)
    
    def update_progress_fill_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.6, 0.8, 1)
            Rectangle(size=instance.size, pos=instance.pos)
    
    def show_add_popup(self, instance):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        name_label = Label(text='目标名称:', font_name=CHINESE_FONT, font_size=16)
        self.name_input = TextInput(hint_text='请输入目标名称', font_size=16, font_name=CHINESE_FONT)
        popup_layout.add_widget(name_label)
        popup_layout.add_widget(self.name_input)
        
        amount_label = Label(text='目标金额:', font_name=CHINESE_FONT, font_size=16)
        self.amount_input = TextInput(hint_text='请输入目标金额', input_filter='float', font_size=16, font_name=CHINESE_FONT)
        popup_layout.add_widget(amount_label)
        popup_layout.add_widget(self.amount_input)
        
        button_box = BoxLayout(spacing=10)
        cancel_button = Button(text='取消', size_hint_x=0.5, height=40, font_name=CHINESE_FONT, font_size=16)
        confirm_button = Button(text='确认', size_hint_x=0.5, height=40, background_color=(0.2, 0.6, 0.8, 1), font_name=CHINESE_FONT, font_size=16)
        button_box.add_widget(cancel_button)
        button_box.add_widget(confirm_button)
        popup_layout.add_widget(button_box)
        
        self.popup = Popup(title='添加新目标', content=popup_layout, size_hint=(0.85, 0.6))
        self.popup.title_font = CHINESE_FONT
        
        cancel_button.bind(on_press=self.popup.dismiss)
        confirm_button.bind(on_press=self.add_goal)
        
        self.popup.open()
    
    def add_goal(self, instance):
        name = self.name_input.text.strip()
        amount_text = self.amount_input.text.strip()
        
        if not name:
            self.show_error('请输入目标名称')
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                self.show_error('目标金额必须大于0')
                return
        except ValueError:
            self.show_error('请输入有效的金额')
            return
        
        self.goals.append({'name': name, 'target': amount, 'current': 0})
        self.save_goals()
        self.refresh_goals_list()
        self.popup.dismiss()
    
    def show_add_amount_popup(self, index):
        goal = self.goals[index]
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        label = Label(text='为 ' + goal["name"] + ' 添加金额', font_name=CHINESE_FONT, font_size=16)
        popup_layout.add_widget(label)
        
        self.amount_add_input = TextInput(hint_text='请输入金额', input_filter='float', font_size=16, font_name=CHINESE_FONT)
        popup_layout.add_widget(self.amount_add_input)
        
        button_box = BoxLayout(spacing=10)
        cancel_button = Button(text='取消', size_hint_x=0.5, height=40, font_name=CHINESE_FONT, font_size=16)
        confirm_button = Button(text='确认', size_hint_x=0.5, height=40, background_color=(0.3, 0.7, 0.3, 1), font_name=CHINESE_FONT, font_size=16)
        button_box.add_widget(cancel_button)
        button_box.add_widget(confirm_button)
        popup_layout.add_widget(button_box)
        
        self.add_amount_popup = Popup(title='添加金额', content=popup_layout, size_hint=(0.85, 0.5))
        self.add_amount_popup.title_font = CHINESE_FONT
        
        cancel_button.bind(on_press=self.add_amount_popup.dismiss)
        confirm_button.bind(on_press=lambda _, idx=index: self.add_amount(idx))
        
        self.add_amount_popup.open()
    
    def add_amount(self, index):
        amount_text = self.amount_add_input.text.strip()
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                self.show_error('金额必须大于0')
                return
        except ValueError:
            self.show_error('请输入有效的金额')
            return
        
        self.goals[index]['current'] += amount
        self.save_goals()
        self.refresh_goals_list()
        self.add_amount_popup.dismiss()
    
    def delete_goal(self, index):
        # 创建美观的删除确认对话框
        popup_layout = BoxLayout(orientation='vertical', padding=25, spacing=20)
        
        # 警告图标
        icon_label = Label(
            text='⚠️', 
            font_size=48, 
            size_hint_y=None, 
            height=60
        )
        popup_layout.add_widget(icon_label)
        
        # 提示文字
        message_label = Label(
            text='确定要删除这个目标吗？', 
            font_name=CHINESE_FONT, 
            font_size=18,
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=40
        )
        popup_layout.add_widget(message_label)
        
        # 目标名称
        goal_name_label = Label(
            text='"' + self.goals[index]["name"] + '"', 
            font_name=CHINESE_FONT, 
            font_size=16,
            color=(0.8, 0.3, 0.3, 1),
            size_hint_y=None,
            height=30
        )
        popup_layout.add_widget(goal_name_label)
        
        # 提示信息
        hint_label = Label(
            text='删除后将无法恢复', 
            font_name=CHINESE_FONT, 
            font_size=13,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=25
        )
        popup_layout.add_widget(hint_label)
        
        # 按钮容器
        button_box = BoxLayout(spacing=15, size_hint_y=None, height=50)
        
        # 取消按钮
        cancel_button = Button(
            text='取消', 
            size_hint_x=0.5, 
            font_name=CHINESE_FONT, 
            font_size=16,
            background_color=(0.85, 0.85, 0.85, 1),
            color=(0, 0, 0, 1)
        )
        
        # 删除按钮
        confirm_button = Button(
            text='🗑️ 删除', 
            size_hint_x=0.5, 
            font_name=CHINESE_FONT, 
            font_size=16,
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        
        button_box.add_widget(cancel_button)
        button_box.add_widget(confirm_button)
        popup_layout.add_widget(button_box)
        
        # 创建弹出窗口
        self.delete_popup = Popup(
            title='确认删除', 
            content=popup_layout, 
            size_hint=(0.85, 0.5),
            separator_color=(0.9, 0.3, 0.3, 1)
        )
        self.delete_popup.title_font = CHINESE_FONT
        self.delete_popup.title_color = (0.9, 0.3, 0.3, 1)
        self.delete_popup.title_size = 20
        
        cancel_button.bind(on_press=self.delete_popup.dismiss)
        confirm_button.bind(on_press=lambda _, idx=index: self.confirm_delete(idx))
        
        self.delete_popup.open()
    
    def confirm_delete(self, index):
        del self.goals[index]
        self.save_goals()
        self.refresh_goals_list()
        self.delete_popup.dismiss()
    
    def show_error(self, message):
        popup = Popup(title='错误', content=Label(text=message, font_name=CHINESE_FONT, font_size=16), size_hint=(0.7, 0.3))
        popup.title_font = CHINESE_FONT
        popup.open()
    
    def save_goals(self):
        with open('goals.json', 'w', encoding='utf-8') as f:
            json.dump(self.goals, f, ensure_ascii=False)
    
    def load_goals(self):
        if os.path.exists('goals.json'):
            try:
                with open('goals.json', 'r', encoding='utf-8') as f:
                    self.goals = json.load(f)
            except:
                self.goals = []
        else:
            self.goals = []

if __name__ == '__main__':
    GoalApp().run()