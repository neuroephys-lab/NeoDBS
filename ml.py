import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# === 1. Data input ===
data = {
    'Current (mA)': [0, 0, 0, 2, 2.5, 3, 2, 3, 2, 2.5, 3, 2],
    'Pulse Width (µs)': [60, 60, 210, 210, 210, 210, 210, 210, 210, 210, 210, 210],
    'Frequency (Hz)': [125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 130, 130],
    'Stimulating Channel': ['1', '1', '1', '1', '2', '2', '2', '2&3', '2&3', '2&3', '2&3', '2&3'],
    'Y-BOCS': [26, 26, 26, 26, 26, 26, 25, 26, 24, 26, 26, 22]
}
df = pd.DataFrame(data)

# === 2. One-hot encode categorical column ===
df_encoded = pd.get_dummies(df, columns=['Stimulating Channel'])

# === 3. Define features and target ===
X = df_encoded.drop(columns=['Y-BOCS'])
y = df_encoded['Y-BOCS']

# === 4. Split for final evaluation ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === 5. Train model ===
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# === 6. Cross-validation ===
cv = KFold(n_splits=5, shuffle=True, random_state=42)
r2_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
mae_scores = -cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error')

print("Cross-validated R² scores:", r2_scores)
print("Average R²:", np.mean(r2_scores))
print("Cross-validated MAE scores:", mae_scores)
print("Average MAE:", np.mean(mae_scores))

# === 7. Feature importances plot ===
importances = model.feature_importances_
feature_names = X.columns
plt.figure(figsize=(8, 4))
plt.barh(feature_names, importances)
plt.xlabel("Feature Importance")
plt.title("Random Forest Feature Importance")
plt.tight_layout()
plt.show()

# === 8. Predict Y-BOCS from new stimulation parameters ===
# Example: Current=2.5, Pulse Width=210, Frequency=125, Channel='2&3'
new_input = pd.DataFrame([{
    'Current (mA)': 2.5,
    'Pulse Width (µs)': 210,
    'Frequency (Hz)': 125,
    'Stimulating Channel_1': 0,
    'Stimulating Channel_2': 0,
    'Stimulating Channel_2&3': 1
}])

predicted_ybocs = model.predict(new_input)[0]
print(f"\n🔮 Predicted Y-BOCS for input [2.5 mA, 210 µs, 125 Hz, Channel 2&3]: {predicted_ybocs:.2f}")
