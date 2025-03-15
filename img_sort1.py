import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel,
                             QGridLayout, QPushButton, QFileDialog, QCheckBox,
                             QScrollArea, QVBoxLayout, QWidget, QHBoxLayout)  # Add QHBoxLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from PIL import Image
import shutil
import json

class ImageCategorizer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image_paths = []
        self.current_image_index = 0
        self.category_directories = {}
        self.category_checkboxes = {}  # Add this to store checkboxes
        self.master_list_file = "master_list.json"
        self.checkbox_count = 0  # Rename from button_count
        self.thumbnail_size = 128 # Add thumbnail size constant
        self.category_thumbnails = {}  # Dictionary to store thumbnail widgets for each category
        self.max_thumbnails = 6

    def initUI(self):
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        self.load_images_button = QPushButton("Get Images from ", self)
        self.load_images_button.clicked.connect(self.loadImages)
        self.grid.addWidget(self.load_images_button, 0, 0)

        self.add_category_button = QPushButton("Send Images to", self)
        self.add_category_button.clicked.connect(self.addCategoryDirectory)
        self.grid.addWidget(self.add_category_button, 0, 2)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(800, 600)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        self.grid.addWidget(self.image_label, 1, 1)

        # Create container for thumbnail areas
        self.thumbs_container = QWidget()
        self.thumbs_layout = QGridLayout(self.thumbs_container)
        self.grid.addWidget(self.thumbs_container, 1, 0)

        # Move button container to last column
        self.button_container = QWidget()
        self.button_container.setFixedHeight(200)  # Set fixed height for button area
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_layout.setSpacing(5)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center buttons vertically
        
        # Add Send button at the top of the container
        self.send_button = QPushButton("Send to Selected", self)
        self.send_button.clicked.connect(self.sendToSelected)
        self.send_button.setFixedHeight(40)
        self.button_layout.addWidget(self.send_button)
        
        # Add container to grid with vertical center alignment
        self.grid.addWidget(self.button_container, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        # Add navigation buttons container
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        
        self.prev_button = QPushButton("Previous", self)
        self.prev_button.clicked.connect(self.previousImage)
        self.prev_button.setEnabled(False)
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.nextImage)
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.next_button)
        
        self.grid.addWidget(nav_container, 2, 1)  # Add below image

        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle('Image Categorizer')
        self.show()

    def loadImages(self):
        image_folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if image_folder:
            files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.image_paths = [(os.path.join(image_folder, f), False) for f in files]
            if self.image_paths:
                self.current_image_index = 0
                self.loadImage(self.image_paths[0][0])
                self.updateNavigationButtons()
                self.saveMasterList()

    def saveMasterList(self):
        with open(self.master_list_file, 'w') as f:
            json.dump(self.image_paths, f)

    def loadMasterList(self):
        if os.path.exists(self.master_list_file):
            with open(self.master_list_file, 'r') as f:
                self.image_paths = json.load(f)
            
            # Don't need to load thumbnails here anymore as they're per-category
            self.loaded_images = [img for img in self.image_paths if not img[1]]
            if self.loaded_images:
                self.current_image_index = 0
                self.loadImage(self.loaded_images[0][0])

    def loadImage(self, image_path):
        img = Image.open(image_path)
        img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                    Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def addCategoryDirectory(self):
        category_folder = QFileDialog.getExistingDirectory(self, "Select Category Directory")
        if category_folder:
            category_name = os.path.basename(category_folder)
            if category_name not in self.category_directories:
                self.category_directories[category_name] = category_folder
                
                # Create scroll area for this category
                scroll = QScrollArea(self)
                scroll.setWidgetResizable(True)
                scroll.setFixedWidth(800)
                
                thumb_widget = QWidget()
                thumb_layout = QHBoxLayout(thumb_widget)  # Change to QHBoxLayout
                thumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Align to left
                scroll.setWidget(thumb_widget)
                
                # Add category label
                label = QLabel(category_name)
                self.thumbs_layout.addWidget(label, self.checkbox_count * 2, 0)
                self.thumbs_layout.addWidget(scroll, self.checkbox_count * 2 + 1, 0)
                
                # Store the thumbnail layout for later use
                self.category_thumbnails[category_name] = {
                    'layout': thumb_layout,
                    'thumbnails': []
                }
                
                # Add checkbox
                checkbox = QCheckBox(category_name, self)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        spacing: 10px;
                        font-size: 16px;
                    }
                    QCheckBox::indicator {
                        width: 26px;
                        height: 26px;
                    }
                """)
                self.category_checkboxes[category_name] = checkbox
                self.button_layout.addWidget(checkbox)  # Changed from button_layout.addWidget with position
                self.checkbox_count += 1

    def addThumbnail(self, image_path, category_name):
        if category_name not in self.category_thumbnails:
            return
            
        thumb_info = self.category_thumbnails[category_name]
        
        # Create thumbnail
        img = Image.open(image_path)
        img.thumbnail((self.thumbnail_size, self.thumbnail_size))
        img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Create label
        thumb_label = QLabel()
        thumb_label.setPixmap(pixmap)
        
        # Add to layout and thumbnails list at the end (right side)
        thumb_info['layout'].addWidget(thumb_label)
        thumb_info['thumbnails'].append(thumb_label)
        
        # Remove oldest thumbnail if we exceed max
        if len(thumb_info['thumbnails']) > self.max_thumbnails:
            oldest = thumb_info['thumbnails'].pop(0)
            oldest.setParent(None)
            oldest.deleteLater()
        
        # Find the scroll area for this category and scroll to the right
        for i in range(self.thumbs_layout.count()):
            widget = self.thumbs_layout.itemAt(i).widget()
            if isinstance(widget, QScrollArea) and widget.widget().layout() == thumb_info['layout']:
                # Use a timer to scroll after the layout is updated
                QTimer.singleShot(100, lambda: widget.horizontalScrollBar().setValue(
                    widget.horizontalScrollBar().maximum()
                ))
                break

    def updateNavigationButtons(self):
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.image_paths) - 1)

    def previousImage(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.loadImage(self.image_paths[self.current_image_index][0])
            self.updateNavigationButtons()

    def nextImage(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.loadImage(self.image_paths[self.current_image_index][0])
            self.updateNavigationButtons()

    def sendToSelected(self):
        if not self.image_paths:
            return
            
        image_path = self.image_paths[self.current_image_index][0]
        copied = False
        
        for category_name, checkbox in self.category_checkboxes.items():
            if checkbox.isChecked():
                destination_folder = self.category_directories[category_name]
                shutil.copy2(image_path, destination_folder)
                self.addThumbnail(image_path, category_name)
                checkbox.setChecked(False)
                copied = True
        
        # Mark current image as processed and move to next
        self.image_paths[self.current_image_index] = (image_path, True)
        self.current_image_index += 1
        if self.current_image_index < len(self.image_paths):
            self.loadImage(self.image_paths[self.current_image_index][0])
            self.updateNavigationButtons()
        else:
            self.image_label.clear()
            self.updateNavigationButtons()
        self.saveMasterList()

def main():
    app = QApplication(sys.argv)
    ex = ImageCategorizer()
    ex.loadMasterList()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()