import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle

print("🌱 Generating Agricultural Dataset (Now with Rainfall)...")

# 1. Generate Synthetic Data for 5 Crops
np.random.seed(42)
samples_per_crop = 200

data = {
    'N': np.concatenate([
        np.random.randint(60, 100, samples_per_crop), # Rice (High N)
        np.random.randint(20, 60, samples_per_crop),  # Wheat (Med N)
        np.random.randint(100, 140, samples_per_crop),# Cotton (Very High N)
        np.random.randint(80, 120, samples_per_crop), # Sugarcane (High N)
        np.random.randint(10, 40, samples_per_crop)   # Groundnut (Low N)
    ]),
    'P': np.concatenate([
        np.random.randint(35, 60, samples_per_crop),  # Rice
        np.random.randint(40, 70, samples_per_crop),  # Wheat
        np.random.randint(30, 60, samples_per_crop),  # Cotton
        np.random.randint(40, 80, samples_per_crop),  # Sugarcane
        np.random.randint(20, 50, samples_per_crop)   # Groundnut
    ]),
    'K': np.concatenate([
        np.random.randint(35, 45, samples_per_crop),  # Rice
        np.random.randint(30, 50, samples_per_crop),  # Wheat
        np.random.randint(25, 40, samples_per_crop),  # Cotton
        np.random.randint(40, 60, samples_per_crop),  # Sugarcane
        np.random.randint(20, 40, samples_per_crop)   # Groundnut
    ]),
    'temperature': np.concatenate([
        np.random.uniform(20, 40, samples_per_crop),  # Rice
        np.random.uniform(15, 30, samples_per_crop),  # Wheat
        np.random.uniform(22, 35, samples_per_crop),  # Cotton
        np.random.uniform(25, 40, samples_per_crop),  # Sugarcane
        np.random.uniform(20, 35, samples_per_crop)   # Groundnut
    ]),
    'humidity': np.concatenate([
        np.random.uniform(80, 100, samples_per_crop), # Rice (Needs water)
        np.random.uniform(40, 70, samples_per_crop),  # Wheat
        np.random.uniform(60, 85, samples_per_crop),  # Cotton
        np.random.uniform(70, 90, samples_per_crop),  # Sugarcane
        np.random.uniform(40, 65, samples_per_crop)   # Groundnut
    ]),
    'ph': np.concatenate([
        np.random.uniform(5.0, 7.5, samples_per_crop),# Rice
        np.random.uniform(5.5, 7.5, samples_per_crop),# Wheat
        np.random.uniform(5.8, 8.0, samples_per_crop),# Cotton
        np.random.uniform(6.0, 7.5, samples_per_crop),# Sugarcane
        np.random.uniform(6.0, 7.0, samples_per_crop) # Groundnut
    ]),
    # ✅ NEW RAINFALL DATA ADDED HERE
    'rainfall': np.concatenate([
        np.random.uniform(200, 300, samples_per_crop), # Rice (High Rain)
        np.random.uniform(70, 150, samples_per_crop),  # Wheat
        np.random.uniform(60, 120, samples_per_crop),  # Cotton
        np.random.uniform(150, 250, samples_per_crop), # Sugarcane
        np.random.uniform(40, 100, samples_per_crop)   # Groundnut
    ]),
    'crop': (['Rice'] * samples_per_crop + 
             ['Wheat'] * samples_per_crop + 
             ['Cotton'] * samples_per_crop + 
             ['Sugarcane'] * samples_per_crop + 
             ['Groundnut'] * samples_per_crop)
}

df = pd.DataFrame(data)

# 2. Split Data (Now includes 'rainfall')
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['crop']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Train the Model
print("🧠 Training Random Forest Model (7 Features)...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 4. Test Accuracy
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy: {accuracy * 100:.2f}%")

# 5. Export the Model
with open('crop_model.pkl', 'wb') as file:
    pickle.dump(model, file)
print("💾 Model saved successfully as 'crop_model.pkl'")