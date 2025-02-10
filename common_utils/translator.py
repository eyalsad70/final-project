
import pandas as pd
#from googletrans import Translator
from deep_translator import GoogleTranslator
import time
from common_utils.local_logger import logger
import re

# Initialize the translator
#translator = Translator()

translate_counter = 0

#print(GoogleTranslator().get_supported_languages())

def is_mostly_english(text):
    # Handle common non-English or special cases like 'N/A'
    if text.strip().lower() in ["n/a", "na", "unknown", "none"]:
        return True 
    return bool(re.match(r'^[A-Za-z0-9\s.,!?\'"|\-]+$', text))

###
###  IMPORTANT NOTE: GoogleTranslator is NOT always stable and may give 500 errors. therefore we translate only if source is not english
###


def translate_text(text, src_lang='auto', dest_lang='en'):
    global translate_counter  # Declare that you're using the global variable
    try:
        if not text or str(text).strip() == "":  # Handle empty values
            return ""
        translated_text = text
        
        if (dest_lang != 'en') or not is_mostly_english(text):
            result_text =  GoogleTranslator(source=src_lang, target=dest_lang).translate(text)
            if result_text.lower().startswith("error"):
                logger.warning(f"Failed to translate text {text}. got error {result_text}")
            else:
                translated_text = result_text
                
 #       translated_texts_list.append(tmp_translate)
        translate_counter += 1
        if not translate_counter % 20:
            time.sleep(1)   # this is needed to prevent bursts on translator, which may cause errors
        return translated_text   
    except Exception as e:
        logger.warning(f"Error translating text {text}: {e}")
        return text  # Return the original text if translation fails


# Function to translate CSV with dynamic languages
def translate_csv(file_name, has_header=True, columns_to_translate=None, src_lang='auto', dest_lang='en'):
     # Read the CSV file
    if has_header:
        df = pd.read_csv(file_name)
    else:
        df = pd.read_csv(file_name, header=None)
      
    # Translate the header (if it exists)
    if has_header:
        df.columns = [translate_text(col, src_lang, dest_lang) for col in df.columns]

    # If no specific columns are provided, translate the entire dataframe
    if columns_to_translate is None:
        columns_to_translate = df.columns.tolist()
    
     # Loop through each column to translate only the specified columns
    for column in columns_to_translate:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: translate_text(x, src_lang, dest_lang))
   
    # Save the translated DataFrame to a new CSV file
    output_file = f'translated_{file_name}'
    df.to_csv(output_file, index=False)

    print(f"Translation completed and saved to '{output_file}'")


if __name__ == "__main__":
    # Example usage for translating user-provided text:
    translated_text = translate_text("שלום, איך אתה?", src_lang='iw', dest_lang='en')
    print("Translated Text:", translated_text)

    # Example usage for translating CSV:
#    translate_csv('delek_gas_stations.csv', True, src_lang='iw', dest_lang='en')
#    translate_csv('dor_gas_stations.csv', True, src_lang='iw', dest_lang='en')
    columns_to_translate = ['name', 'Address', 'city']
    translate_csv('paz_stations.csv', True, columns_to_translate, src_lang='iw', dest_lang='en')