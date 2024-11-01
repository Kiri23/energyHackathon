import pandas as pd


def filter_by_municipio(municipio='CAGUAS'):
    try:
        # Leer el CSV original
        print("Leyendo archivo original...")
        df = pd.read_csv('normalized_outage_data.v2fixed.csv')

        print(f"Total de registros originales: {len(df)}")

        # Filtrar datos de Caguas
        df_municipio = df[df['orig_outage_location_muni'] == municipio]

        # Guardar el nuevo CSV
        output_file = f'{municipio.lower()}_outages.csv'
        df_municipio.to_csv(output_file, index=False)

        print(f"\nEstadísticas del filtrado:")
        print(f"Registros totales en ${municipio}: {len(df_municipio)}")
        print(
            f"Localizaciones únicas: {df_municipio['orig_outage_location_name'].nunique()}")
        print(f"\nArchivo guardado como: {output_file}")

        # Mostrar las primeras localidades con más apagones
        print("\nTop 10 localidades con más apagones:")
        print(
            df_municipio['orig_outage_location_name'].value_counts().head(10))

    except FileNotFoundError:
        print("Error: No se encontró el archivo de entrada 'normalized_outage_data.v2fixed.csv'")
    except Exception as e:
        print(f"Error durante el procesamiento: {e}")


if __name__ == "__main__":
    filter_by_municipio()
