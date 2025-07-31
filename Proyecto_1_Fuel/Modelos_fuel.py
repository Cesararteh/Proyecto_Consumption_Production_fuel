##REALIZAMOS LA CONECCION CON SQL

import pandas as pd
from sqlalchemy import create_engine

# Parámetros de conexión a MySQL
usuario = '***'
clave = '***'
host = 'localhost'
base = 'fuel_database'

# Crear motor de conexión con charset utf8mb4
engine = create_engine(f"mysql+pymysql://{usuario}:{clave}@{host}/{base}?charset=utf8mb4")

# Cargar tabla principal con las columnas necesarias
query_fuel = """
SELECT Year, Country, Coal_consumption, Oil_consumption, Gas_consumption, Coal_production, Oil_production, Gas_production, Population, id_country
FROM database_fuel
"""
df_fuel = pd.read_sql(query_fuel, engine)

# Cargar tabla de países con la columna "condicion"
query_country = """
SELECT id_country, Country, Criterio_regresion
FROM table_country
"""
df_country = pd.read_sql(query_country, engine)

# Realizar el JOIN entre ambas tablas usando id_country
df_joined = pd.merge(df_fuel, df_country, on='id_country', how='inner')


def tabla_paises_habilitados(df_country):
    """
    Devuelve una tabla con los países habilitados y su criterio de regresión.
    """
    df_habilitado = df_country[df_country['Criterio_regresion'] == 'Habilitado'][['Country', 'Criterio_regresion']]
    return df_habilitado

df_habilitado = tabla_paises_habilitados(df_country)

cantidad_paises_unicos = df_habilitado['Country'].nunique()
print(f"Hay {cantidad_paises_unicos} países habilitados para regresión bajo un criterio de 20 años continuos como mínimo.")


# Filtrar solo los países habilitados para regresión
df_base = df_joined[df_joined['Criterio_regresion'] == 'Habilitado'].copy()


##MODELO ECONOMÉTRICO

from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

df_base.loc[:, 'C_Coal_pc'] = df_base['Coal_consumption'] / df_base['Population']
df_base.loc[:, 'C_Oil_pc'] = df_base['Oil_consumption'] / df_base['Population']
df_base.loc[:, 'C_Gas_pc'] = df_base['Gas_consumption'] / df_base['Population']
df_base.loc[:, 'P_Coal_pc'] = df_base['Coal_production'] / df_base['Population']
df_base.loc[:, 'P_Oil_pc'] = df_base['Oil_production'] / df_base['Population']
df_base.loc[:, 'P_Gas_pc'] = df_base['Gas_production'] / df_base['Population']


# 👤 Ingreso del país a analizar
pais_usuario = input("🔎 Ingresa el nombre del país que deseas analizar: ")

# Filtrar el DataFrame por país
df_pais = df_base[df_base['Country_x'] == pais_usuario]

# Verificar si existen datos
if df_pais.empty:
    print(f"❌ No se encontraron datos para el país '{pais_usuario}'. Verifica el nombre o si está habilitado.")
else:
    print(f"✅ Datos encontrados para {pais_usuario}. Registros: {len(df_pais)}")

    # -------------------------
    # Elegir tipo de energía
    # -------------------------
    print("💡 Energías disponibles: Coal, Oil, Gas")
    tipo = input("👉 Escribe el tipo de energía (Coal, Oil o Gas): ").capitalize()

    # Validar tipo ingresado
    if tipo not in ['Coal', 'Oil', 'Gas']:
        print("❌ Tipo de energía no válido.")
    else:
        # Variables para consumo y producción
        var_consumo = f'C_{tipo}_pc'
        var_produccion = f'P_{tipo}_pc'
        
        # Asegurar que existan las columnas
        if var_consumo not in df_pais.columns or var_produccion not in df_pais.columns:
            print("❌ Las columnas per cápita no existen. Asegúrate de haber calculado previamente.")
        else:
            X = df_pais[['Year']]  # variable independiente (2D)

            # -------------------------
            # Modelo para consumo
            # -------------------------
            y_consumo = df_pais[var_consumo]
            modelo_c = LinearRegression().fit(X, y_consumo)
            y_pred_c = modelo_c.predict(X)
            # Añadir constante para el intercepto
            X_sm = sm.add_constant(X)
            # Modelo econométrico con statsmodels para consumo
            modelo_c_stats = sm.OLS(y_consumo, X_sm).fit()
            print("\n📊 Resultados econométricos - Consumo:")
            print(modelo_c_stats.summary())

            # -------------------------
            # Modelo para producción
            # -------------------------
            y_produccion = df_pais[var_produccion]
            modelo_p = LinearRegression().fit(X, y_produccion)
            y_pred_p = modelo_p.predict(X)
            y_produccion = df_pais[var_produccion]
            modelo_p = LinearRegression().fit(X, y_produccion)
            y_pred_p = modelo_p.predict(X)

            # Modelo econométrico con statsmodels para producción
            modelo_p_stats = sm.OLS(y_produccion, X_sm).fit()
            print("\n📊 Resultados econométricos - Producción:")
            print(modelo_p_stats.summary())

            # -------------------------
            # Gráficas
            # -------------------------
            fig, axs = plt.subplots(2, 1, figsize=(10, 10))  # dos filas, una columna

            # Gráfico de consumo
            axs[0].plot(X, y_consumo, 'o', label='Consumo real')
            axs[0].plot(X, y_pred_c, '-', color='red', label='Regresión lineal')
            axs[0].set_title(f'{tipo} - Consumo per cápita en {pais_usuario}')
            axs[0].set_xlabel('Año')
            axs[0].set_ylabel('Consumo per cápita')
            axs[0].legend()
            axs[0].grid(True)

            # Gráfico de producción
            axs[1].plot(X, y_produccion, 'o', label='Producción real')
            axs[1].plot(X, y_pred_p, '-', color='green', label='Regresión lineal')
            axs[1].set_title(f'{tipo} - Producción per cápita en {pais_usuario}')
            axs[1].set_xlabel('Año')
            axs[1].set_ylabel('Producción per cápita')
            axs[1].legend()
            axs[1].grid(True)

            # Ajuste final y mostrar
            plt.tight_layout()
            plt.show()
            # 🔮 Extrapolación al año 2025
            año_extrapolado = 2025
            X_future = pd.DataFrame({'Year': [año_extrapolado]})
            # Predicción con modelos sklearn
            consumo_2025 = modelo_c.predict(X_future)[0]
            produccion_2025 = modelo_p.predict(X_future)[0]

            print(f"\n📈 Predicción para el año {año_extrapolado} en {pais_usuario}:")
            print(f" {tipo} - Consumo per cápita estimado: {consumo_2025:.4f}")
            print(f" {tipo} - Producción per cápita estimada: {produccion_2025:.4f}")
