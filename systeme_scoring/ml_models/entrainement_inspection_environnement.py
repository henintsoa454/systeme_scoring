import pandas as pd
from sklearn.calibration import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import OrdinalEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Charger les données
data = pd.read_csv("../data/donnees_inspection_environnement_score.csv")

encoder = LabelEncoder()
data["statut_juridique"] = encoder.fit_transform(data["statut_juridique"])

# Ordres pour l'encodage ordinal
ordinal_mappings = {
    "etat_locaux": [["excellent", "bon", "moyen", "mediocre"]],
    "systeme_gestion": [["informatise", "manuel"]],
    "niveau_concurrence": [["faible", "moyen", "fort"]],
}

ordinal_encoder = OrdinalEncoder(categories=[
    ordinal_mappings["etat_locaux"][0],
    ordinal_mappings["systeme_gestion"][0],
    ordinal_mappings["niveau_concurrence"][0],
])

ordinal_features = list(ordinal_mappings.keys())
data[ordinal_features] = ordinal_encoder.fit_transform(data[ordinal_features])

X = data.drop(columns=['score_inspection'])
y = data['score_inspection']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Définir les modèles
models = {
    "Linear Regression": LinearRegression(),
    "Gradient Boosting": GradientBoostingRegressor(random_state=42),
    "K-Neighbors Regressor": KNeighborsRegressor(n_neighbors=5)
}

# Entraîner les modèles et évaluer les performances
model_results = {}
print("Entraînement des modèles :\n")
for name, model in models.items():
    print(f"-> {name}")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    # Calcul des métriques
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    model_results[name] = {"R²": r2, "MSE": mse}
    print(f"{name} - R²: {r2:.2f}, MSE: {mse:.2f}")

# Résultats des modèles
results_df = pd.DataFrame(model_results).T
print("\nRésultats des modèles :")
print(results_df)

# Sélectionner le meilleur modèle basé sur le R²
best_model_name = max(model_results, key=lambda name: model_results[name]["R²"])
best_model = models[best_model_name]
print(f"\nMeilleur modèle : {best_model_name}")

# Comparaison des valeurs réelles et prédites pour le meilleur modèle
y_pred = best_model.predict(X_test)
plt.figure(figsize=(10, 6))
sns.regplot(x=y_test, y=y_pred, line_kws={'color': 'red'}, scatter_kws={'s': 10})
plt.xlabel('Valeurs réelles')
plt.ylabel('Valeurs prédites')
plt.title(f'Comparaison des valeurs réelles et prédites ({best_model_name})')
plt.show()

# Importance des caractéristiques (si applicable)
if hasattr(best_model, 'feature_importances_'):
    feature_importances = best_model.feature_importances_
    features = X.columns
    plt.figure(figsize=(10, 6))
    sns.barplot(x=feature_importances, y=features)
    plt.title('Importance des caractéristiques')
    plt.xlabel('Importance')
    plt.ylabel('Caractéristiques')
    plt.show()
else:
    print(f"Le modèle {best_model_name} ne supporte pas l\'importance des caractéristiques.")

# Validation croisée
print("\nValidation croisée (5-fold) pour le meilleur modèle :")
cross_val_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='r2')
print(f"R² moyen (CV): {cross_val_scores.mean():.2f}, Écart-type: {cross_val_scores.std():.2f}")

# Sauvegarde du meilleur modèle et des encodeurs
joblib.dump(best_model, "modele_inspection_environnement.pkl")
joblib.dump(ordinal_encoder, "ordinal_encoder_inspection_environnement.pkl")
joblib.dump(encoder, "encoder_statut_juridique.pkl")
print("\nLe meilleur modèle et les encodeurs ont été sauvegardés avec succès.")
