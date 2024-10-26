from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                           QSlider, QLabel, QStyle, QFrame)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os

class MediaPlayer(QWidget):
    timestampUpdated = pyqtSignal(float)  # Signal to sync with transcript

    def __init__(self, parent=None):
        super().__init__()
        self.setup_player()
        self.setup_ui()
        self.setup_connections()

    def setup_player(self):
        self.player = QMediaPlayer()
        self.duration = 0

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setFixedSize(32, 32)
        
        # Backward and Forward buttons
        self.backward_button = QPushButton()
        self.backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.backward_button.setFixedSize(32, 32)
        
        self.forward_button = QPushButton()
        self.forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.forward_button.setFixedSize(32, 32)
        
        # Time labels
        self.time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        
        # Volume control
        self.volume_button = QPushButton()
        self.volume_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume_button.setFixedSize(32, 32)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        
        # Add widgets to controls layout
        controls_layout.addWidget(self.backward_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.forward_button)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.progress_slider)
        controls_layout.addWidget(self.total_time_label)
        controls_layout.addWidget(self.volume_button)
        controls_layout.addWidget(self.volume_slider)
        
        # Add layouts to main layout
        layout.addLayout(controls_layout)
        
        # Set fixed height for media player
        self.setFixedHeight(70)  # Adjust this value as needed

    def setup_connections(self):
        # Button connections
        self.play_button.clicked.connect(self.toggle_playback)
        self.backward_button.clicked.connect(lambda: self.seek_relative(-10000))
        self.forward_button.clicked.connect(lambda: self.seek_relative(10000))
        
        # Media player connections
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.stateChanged.connect(self.on_state_changed)
        
        # Slider connections
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        
        # Volume connections
        self.volume_slider.valueChanged.connect(self.player.setVolume)
        self.volume_button.clicked.connect(self.toggle_mute)

    def load_media(self, file_path):
        """Load a media file into the player"""
        if not os.path.exists(file_path):
            return False
            
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        return True

    def toggle_playback(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek_relative(self, offset):
        """Seek relative to current position in milliseconds"""
        position = self.player.position() + offset
        if position < 0:
            position = 0
        if position > self.duration:
            position = self.duration
        self.player.setPosition(position)

    def on_position_changed(self, position):
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)
        self.time_label.setText(self.format_time(position))
        self.timestampUpdated.emit(position / 1000.0)

    def on_duration_changed(self, duration):
        self.duration = duration
        self.progress_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_slider_pressed(self):
        self.was_playing = self.player.state() == QMediaPlayer.PlayingState
        self.player.pause()

    def on_slider_released(self):
        self.player.setPosition(self.progress_slider.value())
        if self.was_playing:
            self.player.play()

    def toggle_mute(self):
        self.player.setMuted(not self.player.isMuted())
        self.volume_button.setIcon(
            self.style().standardIcon(
                QStyle.SP_MediaVolumeMuted if self.player.isMuted() 
                else QStyle.SP_MediaVolume
            )
        )

    @staticmethod
    def format_time(ms):
        """Convert milliseconds to MM:SS format"""
        s = int(ms / 1000)
        m = int(s / 60)
        s = s % 60
        return f"{m:02d}:{s:02d}"

    def cleanup(self):
        """Clean up resources"""
        if self.player:
            self.player.stop()