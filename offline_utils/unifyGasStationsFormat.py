import pandas as pd

# Mapping for Delek
delek_mapping = {
    'joe': 'Store',
    'minta': 'Store',
    'orea': 'Producturea',
    'urea': 'Producturea',
    'electric': 'Iselectric',
}

# Mapping for Dor-Alon
dor_alon_mapping = {
    'uriah': 'Producturea',
    'urea': 'Producturea',
    'mini': 'Store',
    'super': 'Store',
    'Fuel 98': 'Product98',
    'electric': 'Iselectric',
    'washing': 'Car_wash',
}

def convert_to_paz_format(row, store_type='delek'):
    # Initialize all services as False
    services = {
        'Product98': False,
        'Productgas': False,  # Not handled yet, keeping placeholder
        'Producturea': False,
        'Iselectric': False,
        'Car_wash': False,
        'Store': False
    }
    
    # Determine which mapping to apply
    if store_type == 'delek':
        services_mapping = delek_mapping
    elif store_type == 'dor-alon':
        services_mapping = dor_alon_mapping
    else:
        return services  # Return empty if invalid store type

    # Ensure row is a dictionary, then get services text
    if isinstance(row, dict):
        services_text = row.get('Services', '')
    else:
        services_text = str(row)  # If row is not a dictionary, treat it as a string

    # Ensure services_text is a string and split by commas
    services_text = str(services_text).lower().split(',')

    # Strip extra spaces from the services
    services_text = [service.strip() for service in services_text]

    # Check the service string and update services
    for service, mapped_service in services_mapping.items():
        if any(service.lower() in s for s in services_text):  # Match any service in the list
            services[mapped_service] = True

    return services

# Function to apply the conversion to a CSV file
def convert_csv(file_path, store_type='delek'):
    df = pd.read_csv(file_path)
    
    # Assuming 'Services' column contains the service string
    df_services = df['Services'].apply(lambda row: convert_to_paz_format(row, store_type))
    
    # Convert to the appropriate columns and add them to the dataframe
    df_services_df = pd.DataFrame(df_services.tolist(), columns=['Product98', 'Productgas', 'Producturea', 'Iselectric', 'Car_wash', 'Store'])
    df = pd.concat([df, df_services_df], axis=1)
    
    return df


# Example usage:
# Convert Delek CSV to Paz format
delek_df = convert_csv('offline_utils/translated_delek_gas_stations.csv', store_type='delek')
print(delek_df.head())
delek_df.to_csv('offline_utils/delek_stations_transformed.csv', index=False)

# Convert Dor-Alon CSV to Paz format
dor_alon_df = convert_csv('offline_utils/translated_dor_gas_stations.csv', store_type='dor-alon')
print(dor_alon_df.head())
dor_alon_df.to_csv('offline_utils/doralon_stations_transformed.csv', index=False)
