import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np

print("🌿 Building Plant Doctor CNN Architecture...")

# 1. Define our disease classes
classes = ["Healthy Plant", "Late Blight (Fungal)", "Leaf Rust", "Powdery Mildew"]

# 2. Build a Convolutional Neural Network (CNN)
# This mimics a standard image classification architecture
model = models.Sequential([
    # Input layer: Expects a 128x128 pixel RGB image
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    layers.MaxPooling2D((2, 2)),
    
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    layers.Conv2D(64, (3, 3), activation='relu'),
    
    # Flatten the 2D image into a 1D array for the final decision
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    
    # Output layer: 4 nodes for our 4 specific classes
    layers.Dense(len(classes), activation='softmax') 
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 3. Initialize weights (Using dummy data for the MCA project setup)
# In a real-world scenario, you would train this on thousands of leaf images using ImageDataGenerator
print("⏳ Initializing neural weights...")
dummy_x = np.random.rand(10, 128, 128, 3) # 10 fake images
dummy_y = np.random.randint(0, len(classes), 10) # 10 fake labels

# Train for 1 epoch just to compile the structure
model.fit(dummy_x, dummy_y, epochs=1, verbose=0)

# 4. Export the Model
model.save('plant_doctor.h5')
print("✅ Deep Learning Model saved successfully as 'plant_doctor.h5'")